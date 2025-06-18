import os
from typing import Dict, TypedDict, List
from gen_ai_hub.proxy.langchain.init_models import init_llm
from langchain.prompts import PromptTemplate
from langgraph.graph import StateGraph, END
from pydantic import BaseModel
from datetime import datetime
import logging
from tenacity import retry, stop_after_attempt, wait_exponential
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables from .env file (recommended)
load_dotenv()

# Initialize LLM 
llm = init_llm("gpt-4o", max_tokens=4000)  

# Pydantic model for user input validation
class BRDInput(BaseModel):
    project_name: str
    project_purpose: str
    scope_area: str
    in_scope_items: List[str]
    out_of_scope_items: List[str]
    stakeholders: List[str]

# State definition for LangGraph
class BRDState(TypedDict):
    user_input: BRDInput
    draft_brd: str
    validated_brd: str
    error: str

# Input collection function
def collect_user_input() -> BRDInput:
    print("Please provide the following details for BRD generation:")
    project_name = input("Project Name: ").strip()
    project_purpose = input("Project Purpose: ").strip()
    scope_area = input("Scope Area: ").strip()
    
    in_scope_items = []
    print("Enter in-scope items (one per line, press Enter twice to finish):")
    while True:
        item = input().strip()
        if item == "":
            break
        in_scope_items.append(item)
    
    out_of_scope_items = []
    print("Enter out-of-scope items (one per line, press Enter twice to finish):")
    while True:
        item = input().strip()
        if item == "":
            break
        out_of_scope_items.append(item)
    
    stakeholders = []
    print("Enter stakeholders (one per line, press Enter twice to finish):")
    while True:
        stakeholder = input().strip()
        if stakeholder == "":
            break
        stakeholders.append(stakeholder)
    
    try:
        return BRDInput(
            project_name=project_name,
            project_purpose=project_purpose,
            scope_area=scope_area,
            in_scope_items=in_scope_items,
            out_of_scope_items=out_of_scope_items,
            stakeholders=stakeholders
        )
    except ValueError as e:
        raise ValueError(f"Invalid input: {str(e)}")

# BRD generation prompt template
brd_prompt_template = PromptTemplate(
    input_variables=["project_name", "project_purpose", "scope_area", "in_scope_items", "out_of_scope_items", "stakeholders"],
    template="""Generate a Business Requirement Document (BRD) based on the following inputs. Ensure the document is professional, clear, and follows the structure provided. Use Markdown format.

**BRD Structure**:
1. Purpose
2. Project Summary
3. Project Success Criteria
4. Project Objectives
5. In-Scope
6. Out of Scope
7. Non-Functional Requirements
8. Assumptions
9. Dependencies
10. Constraints
11. Stakeholder Analysis
12. Roles and Responsibilities

**Inputs**:
- Project Name: {project_name}
- Project Purpose: {project_purpose}
- Scope Area: {scope_area}
- In-Scope Items: {in_scope_items}
- Out of Scope Items: {out_of_scope_items}
- Stakeholders: {stakeholders}

**Instructions**:
- Use the inputs to fill relevant sections.
- For sections not directly provided (e.g., Success Criteria, Non-Functional Requirements), infer reasonable content based on the inputs and general best practices.
- Ensure all 12 sections are present, clear, and professional.
- Use bullet points for lists and proper headings (##) for sections."""
)

# Validation prompt template
validation_prompt_template = PromptTemplate(
    input_variables=["draft_brd", "user_input"],
    template="""Validate the following Business Requirement Document (BRD) against the provided user inputs and the required structure. Ensure completeness (all 12 sections present), proper structure, and alignment with user inputs. Fill in any missing or incomplete sections with appropriate content. Return the validated BRD in Markdown format.

**Required Structure**:
1. Purpose
2. Project Summary
3. Project Success Criteria
4. Project Objectives
5. In-Scope
6. Out of Scope
7. Non-Functional Requirements
8. Assumptions
9. Dependencies
10. Constraints
11. Stakeholder Analysis
12. Roles and Responsibilities

**User Inputs**:
{user_input}

**Draft BRD**:
{draft_brd}

**Instructions**:
- Validate that all 12 sections are present and follow the structure.
- Check alignment with user inputs:
  - Purpose must match Project Purpose.
  - Project Summary must reflect Scope Area.
  - In-Scope and Out of Scope must match provided items.
  - Stakeholder Analysis and Roles and Responsibilities must include all listed stakeholders.
- If any section is missing, empty, or misaligned, fill it with appropriate content based on user inputs and general best practices (e.g., infer Success Criteria from Scope Area, add standard Non-Functional Requirements).
- Return the validated BRD in Markdown format with all 12 sections complete and aligned."""
)

# Input node
def input_node(state: BRDState) -> BRDState:
    try:
        state["user_input"] = collect_user_input()
        state["error"] = ""
        logger.info("User input collected successfully")
    except Exception as e:
        state["error"] = f"Input collection failed: {str(e)}"
        logger.error(state["error"])
    return state

# BRD generation node
def brd_generation_node(state: BRDState) -> BRDState:
    if state.get("error"):
        return state
    
    try:
        user_input = state["user_input"]
        prompt = brd_prompt_template.format(
            project_name=user_input.project_name,
            project_purpose=user_input.project_purpose,
            scope_area=user_input.scope_area,
            in_scope_items=", ".join(user_input.in_scope_items),
            out_of_scope_items=", ".join(user_input.out_of_scope_items),
            stakeholders=", ".join(user_input.stakeholders)
        )
        response = llm.invoke(prompt)
        state["draft_brd"] = response.content.strip()
        logger.info("Draft BRD generated successfully")
        logger.debug(f"Draft BRD: {state['draft_brd'][:500]}...")  # Log first 500 chars
        state["error"] = ""
    except Exception as e:
        state["error"] = f"BRD generation failed: {str(e)}"
        logger.error(state["error"])
    return state

# BRD validation node with retry
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def brd_validation_node(state: BRDState) -> BRDState:
    if state.get("error"):
        return state
    
    try:
        user_input_str = f"""
        Project Name: {state['user_input'].project_name}
        Project Purpose: {state['user_input'].project_purpose}
        Scope Area: {state['user_input'].scope_area}
        In-Scope Items: {', '.join(state['user_input'].in_scope_items)}
        Out of Scope Items: {', '.join(state['user_input'].out_of_scope_items)}
        Stakeholders: {', '.join(state['user_input'].stakeholders)}
        """
        prompt = validation_prompt_template.format(
            draft_brd=state["draft_brd"],
            user_input=user_input_str
        )
        response = llm.invoke(prompt)
        validated_brd = response.content.strip()
        logger.debug(f"Validation response: {validated_brd[:500]}...")  # Log first 500 chars

        # Verify the validated BRD has all 12 sections
        if len(validated_brd.split("##")) >= 12:
            state["validated_brd"] = validated_brd
            state["error"] = ""
            logger.info("BRD validated successfully")
        else:
            state["validated_brd"] = ""
            state["error"] = "Validation failed: Incomplete BRD returned"
            logger.error(state["error"])
        
    except Exception as e:
        state["error"] = f"BRD validation failed: {str(e)}"
        state["validated_brd"] = ""
        logger.error(state["error"])
    return state

# Output node
def output_node(state: BRDState) -> BRDState:
    if state.get("error"):
        print(f"Error: {state['error']}")
        logger.error(f"Output node error: {state['error']}")
        return state
    
    try:
        # Save validated BRD to file
        if state["validated_brd"]:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"BRD_{state['user_input'].project_name}_{timestamp}.md"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(state["validated_brd"])
            
            print(f"BRD saved to {filename}")
            logger.info(f"BRD saved to {filename}")
        else:
            state["error"] = "No valid BRD to output"
            print(f"Error: {state['error']}")
            logger.error(state["error"])
    except Exception as e:
        state["error"] = f"Output failed: {str(e)}"
        logger.error(state["error"])
    return state

# Build LangGraph workflow
workflow = StateGraph(BRDState)
workflow.add_node("input", input_node)
workflow.add_node("brd_generation", brd_generation_node)
workflow.add_node("brd_validation", brd_validation_node)
workflow.add_node("output", output_node)

# Define edges
workflow.set_entry_point("input")
workflow.add_edge("input", "brd_generation")
workflow.add_edge("brd_generation", "brd_validation")
workflow.add_edge("brd_validation", "output")
workflow.add_edge("output", END)

# Compile and run
graph = workflow.compile()

# Execute the workflow
def run_brd_generation():
    initial_state = BRDState(
        user_input=None,
        draft_brd="",
        validated_brd="",
        error=""
    )
    try:
        result = graph.invoke(initial_state)
        return result
    except Exception as e:
        print(f"Workflow execution failed: {str(e)}")
        logger.error(f"Workflow execution failed: {str(e)}")
        return None

if __name__ == "__main__":
    run_brd_generation()
