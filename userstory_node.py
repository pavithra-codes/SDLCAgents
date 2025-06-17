import os
import asyncio
import json
from typing_extensions import TypedDict
from dotenv import load_dotenv
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import HumanMessage, SystemMessage
from gen_ai_hub.proxy.langchain.init_models import init_llm
from langchain.prompts import ChatPromptTemplate
from langchain.schema.output_parser import StrOutputParser
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

# Define State
class UserStoryState(TypedDict):
    generated_output: str
    validated_output: str
    pdf_path: str

# Load environment variables
load_dotenv()

# Initialize LLM
llm = init_llm("gpt-4o")
llm = llm.bind(max_completion_tokens=None)  # To avoid max_completion_tokens error

# Hardcoded BRD Details
brd_data = {
    "purpose": "The purpose of the oracle to redshift migration project is to modernize the technology stack and leverage AWS cloud capabilities to provide faster analytics and insights.",
    "project_summary": "The project involves recreating the existing data warehouse from an on-premise Oracle database into AWS Redshift. This migration aims to enhance data processing capabilities and improve the efficiency of data analytics.",
    "success_criteria": "1. Successful migration of all specified tables and stored procedures without data loss. 2. Integration of data using AWS Glue and EMR with zero downtime. 3.Achievement of a 25 percent improvement in data processing speed. 4. User acceptance testing (UAT) approval from IT department, marketing teams, and dealers.",
    "objectives": "1. Migrate all relevant tables from the Oracle database to AWS Redshift. 2.Convert and optimize all stored procedures for AWS Redshift.3. Implement data integration processes using AWS Glue and EMR. 4. Ensure data integrity and security during and after migration.",
    "in_scope": "1. Table migration from Oracle to AWS Redshift. 2. Stored procedure migration to AWS Redshift.3. Data integration using AWS Glue and EMR.",
    "out_scope": "1. Infrastructure setup for AWS Redshift. 2. Processing of Personally Identifiable Information (PII) data. 3. Administrative tasks unrelated to direct migration activities.",
    "non_functional": "1. Performance: The system should handle queries at least 25 percent faster than the current Oracle setup. 2. Security: All data must be encrypted during transit and at rest. Compliance with standard data security regulations (e.g., GDPR, HIPAA) is required. 3. Usability: The new system should maintain a user-friendly interface similar to the existing system to minimize training needs.",
    "assumptions": "1. The current Oracle database schema is well-documented and up-to-date. 2. All current data in the Oracle database is accurate and ready for migration.3. Necessary AWS services (Redshift, Glue, EMR) are available and operational. 4. Stakeholders are available for consultation and UAT as per the project schedule.",
    "dependencies": "1. Availability of AWS infrastructure and services. 2. Cooperation from the IT department for technical expertise and support.3. Marketing teams and dealers' availability for UAT and feedback.",
    "constraints": "The project must be completed within a 6-month timeframe. Budget constraints limit the use of additional third-party tools or services. Limited availability of key personnel for project tasks due to other organizational commitments.",
    "stakeholders": "1. IT Department: Responsible for providing technical expertise, support, and validation of the migration process. 2. Marketing Teams: Will provide requirements based on their data analytics needs and participate in UAT.3. Dealers: End-users who will provide feedback on the system performance and usability in UAT.",
    "roles": "1. Project Manager: Oversee project execution, manage timelines, and coordinate between teams. 2. Data Engineers: Responsible for the actual migration of tables and stored procedures, and for setting up data integrations.3. IT Security Team: Ensure compliance with data security requirements. 4. QA Analysts: Conduct thorough testing to ensure the functionality and performance of the new system meet project standards. 5.Stakeholders (Marketing Teams, Dealers): Participate in UAT to validate the system meets their needs."
}

# Generate User Stories Node
def generate_user_stories_node(state: UserStoryState) -> UserStoryState:
    brd_content = json.dumps(brd_data)

    prompt = ChatPromptTemplate.from_messages([
        SystemMessage(content="You are an SAP Functional Consultant. Generate a list of user stories, by breaking down the tasks into multiple smallest possible levels, from the provided BRD content for an SAP project. Each user story must include: Title, Description, Acceptance Criteria, Definition of Done (DoD), and Definition of Ready (DoR). Format each user story clearly and use SAP-specific terminology. Output the user stories in a JSON format where each story is an object with fields 'title', 'description', 'acceptance_criteria', 'definition_of_done', and 'definition_of_ready'."),
        HumanMessage(content=f"BRD Content: {brd_content}")
    ])
    chain = prompt | llm | StrOutputParser()
    generated_output = chain.invoke({"input_data": brd_content})

    return {
        "generated_output": generated_output,
        "validated_output": state["validated_output"],  # Preserve existing value
        "pdf_path": state["pdf_path"]  # Preserve existing value
    }

# Validate User Stories Node
def validate_user_stories_node(state: UserStoryState) -> UserStoryState:
    # Add error handling for missing key
    if "generated_output" not in state:
        raise KeyError("State is missing 'generated_output'. Ensure the 'generate' node ran successfully.")
    generated_output = state["generated_output"]

    prompt = ChatPromptTemplate.from_messages([
        SystemMessage(content="Validate the following user stories for completeness and SAP standards. Ensure each user story includes: Title, Description, Acceptance Criteria, Definition of Done (DoD), and Definition of Ready (DoR). If incomplete, add missing fields with appropriate values for an SAP project. Return the validated user stories in the same JSON format."),
        HumanMessage(content=f"User Stories: {generated_output}")
    ])
    chain = prompt | llm | StrOutputParser()
    validated_output = chain.invoke({"generated_output": generated_output})

    return {
        "generated_output": state["generated_output"],
        "validated_output": validated_output,
        "pdf_path": state["pdf_path"]  # Preserve existing value
    }

# Output PDF Node
def output_pdf_node(state: UserStoryState) -> UserStoryState:
    validated_output = state["validated_output"]

    # Debug: Print the entire state and validated_output to inspect
    print("State in output_pdf_node:")
    print(state)
    print("Validated Output (JSON string):")
    print(validated_output)

    # Clean the validated_output by removing Markdown code block markers
    cleaned_output = validated_output.strip()
    if cleaned_output.startswith("```json"):
        # Remove the ```json at the start and ``` at the end
        cleaned_output = cleaned_output[len("```json"):].strip()
        if cleaned_output.endswith("```"):
            cleaned_output = cleaned_output[:-len("```")].strip()

    # Debug: Print the cleaned output
    print("Cleaned Validated Output (after removing Markdown):")
    print(cleaned_output)

    # Parse JSON output
    try:
        user_stories = json.loads(cleaned_output)
    except json.JSONDecodeError as e:
        print(f"Error parsing cleaned JSON: {e}")
        user_stories = []

    # Debug: Print the parsed user stories
    print("Parsed User Stories:")
    print(user_stories)

    # Create PDF
    pdf_path = "user_stories_output.pdf"
    doc = SimpleDocTemplate(pdf_path, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []

    # Add Title
    elements.append(Paragraph("User Stories", styles["Title"]))
    elements.append(Paragraph("<br/>", styles["Normal"]))  # Spacer

    # Prepare table data
    table_data = [["Title", "Description", "Acceptance Criteria", "Definition of Done", "Definition of Ready"]]
    if isinstance(user_stories, list) and user_stories:
        for story in user_stories:
            # Handle acceptance_criteria and other fields that might be lists
            acceptance_criteria = story.get("acceptance_criteria", "")
            if isinstance(acceptance_criteria, list):
                acceptance_criteria = "; ".join(acceptance_criteria)
            definition_of_done = story.get("definition_of_done", "")
            if isinstance(definition_of_done, list):
                definition_of_done = "; ".join(definition_of_done)
            definition_of_ready = story.get("definition_of_ready", "")
            if isinstance(definition_of_ready, list):
                definition_of_ready = "; ".join(definition_of_ready)

            table_data.append([
                Paragraph(story.get("title", ""), styles["Normal"]),
                Paragraph(story.get("description", ""), styles["Normal"]),
                Paragraph(acceptance_criteria, styles["Normal"]),
                Paragraph(definition_of_done, styles["Normal"]),
                Paragraph(definition_of_ready, styles["Normal"])
            ])
    else:
        print("Warning: No user stories available to display in the table.")
        table_data.append(["No user stories generated.", "", "", "", ""])  # Add a placeholder row

    # Debug: Print the table data
    print("Table Data for PDF:")
    print(table_data)

    # Create table
    table = Table(table_data)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
        ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
        ("GRID", (0, 0), (-1, -1), 1, colors.black),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("WORDWRAP", (0, 0), (-1, -1), "CJK")
    ]))
    elements.append(table)

    # Build PDF
    doc.build(elements)
    print(f"PDF generated at: {pdf_path}")

    return {
        "generated_output": state["generated_output"],
        "validated_output": state["validated_output"],
        "pdf_path": pdf_path
    }

# Define Graph
graph = StateGraph(UserStoryState)

# Add Nodes
graph.add_node("generate", generate_user_stories_node)
graph.add_node("validate", validate_user_stories_node)
graph.add_node("output", output_pdf_node)

# Add Edges
graph.add_edge(START, "generate")
graph.add_edge("generate", "validate")
graph.add_edge("validate", "output")
graph.add_edge("output", END)

# Compile Graph
app = graph.compile()

# Run Graph
initial_state = {
    "generated_output": "",
    "validated_output": "",
    "pdf_path": ""
}

result = app.invoke(initial_state, config={"recursion_limit": 50})

# Final Output
print("Generated User Stories (Raw):")
print(result["generated_output"])
print("\nValidated User Stories:")
print(result["validated_output"])
print("\nPDF Path:")
print(result["pdf_path"])