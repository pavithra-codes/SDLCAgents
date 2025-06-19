from flask import Blueprint, request, render_template, send_from_directory
from langgraph.graph import StateGraph
from langchain_core.runnables import RunnableLambda
from gen_ai_hub.proxy.langchain.init_models import init_llm
from typing import TypedDict
from datetime import datetime
import os
import time
import re
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet

env_vars = {
    'AICORE_AUTH_URL': 'https://genai-ltim.authentication.eu10.hana.ondemand.com/oauth/token',
    'AICORE_CLIENT_ID': 'sb-b66c3931-8480-4dfd-8108-0992e56cac64!b476474|aicore!b540',
    'AICORE_CLIENT_SECRET': 'edf7fec3-428d-4983-b574-536143d70001$I7GPwBkjWwNnKDZmo7PQ3MZ0w4sDNKtO3pOpYKReCZU=',
    'AICORE_BASE_URL': 'https://api.ai.prod.eu-central-1.aws.ml.hana.ondemand.com/v2',
    'AICORE_RESOURCE_GROUP': 'default'
}
for key, value in env_vars.items():
    os.environ[key] = value

# Initialize GPT-4o
llm = init_llm("gpt-4o")
llm = llm.bind(max_completion_tokens=None)

class ABAPDocState(TypedDict):
    abap_code: str
    output: str

development_bp = Blueprint("development", __name__)

def clean_output_for_pdf(text: str) -> str:
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
    text = re.sub(r"#{1,6}\s*", "", text)
    return text

# Saving output PDF in local directory
def save_pdf(raw_text: str) -> str:
    styles = getSampleStyleSheet()
    save_dir = r"C:\Users\10828991\OneDrive - LTIMindtree\Desktop\langgraph task"
    os.makedirs(save_dir, exist_ok=True)

    filename = f"ABAP_Documentation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    pdf_path = os.path.join(save_dir, filename)

    doc = SimpleDocTemplate(pdf_path, pagesize=letter)
    elements = [Paragraph("ABAP Documentation", styles['Title'])]

    cleaned = clean_output_for_pdf(raw_text)
    for line in cleaned.split("\n"):
        if line.strip():
            elements.append(Paragraph(line.strip(), styles["Normal"]))

    doc.build(elements)
    return pdf_path

# Validate output 
def validate_output(output: str) -> bool:
    required_sections = [
        "Technical Documentation",
        "Code Review Comments",
        "Optimization Suggestions"
    ]
    return all(section in output for section in required_sections)

# Documentation generation
def generate_abap_doc(state: ABAPDocState) -> ABAPDocState:
    abap_code = state["abap_code"]
    prompt = f"""
You are an expert SAP ABAP code reviewer and documentation generator.

Given the following ABAP code, provide:
1. Technical Documentation (purpose, inputs, outputs, logic, tables used)
2. Code Review Comments
3. Optimization Suggestions (performance, readability, best practices)

ABAP Code:
{abap_code}
"""

    for attempt in range(5):
        try:
            response = llm.invoke(prompt)
            return {"output": response.content, "abap_code": abap_code}
        except Exception as e:
            print(f"[Retry {attempt + 1}] Error: {e}")
            time.sleep(2 ** attempt)

    return {"output": "Error generating documentation.", "abap_code": abap_code}

# LangGraph 
graph_builder = StateGraph(ABAPDocState)
graph_builder.add_node("generate_doc", RunnableLambda(generate_abap_doc))
graph_builder.set_entry_point("generate_doc")
graph_builder.set_finish_point("generate_doc")
graph = graph_builder.compile()

# Flask UI 
@development_bp.route("/", methods=["GET", "POST"])
def development():
    output = None
    message = None
    pdf_filename = None

    if request.method == "POST":
        uploaded_file = request.files["code_file"]
        if uploaded_file and uploaded_file.filename.endswith(".txt"):
            abap_code = uploaded_file.read().decode("utf-8")
            state: ABAPDocState = {"abap_code": abap_code, "output": ""}
            result = graph.invoke(state)
            output = result["output"]

            if validate_output(output):
                pdf_path = save_pdf(output)
                pdf_filename = os.path.basename(pdf_path)
                message = " Documentation generated successfully."
            else:
                message = " Documentation validation failed. Please check the ABAP code or try again."

    return render_template("development.html", output=output, message=message, pdf_filename=pdf_filename)

# location of PDF
@development_bp.route("/download/<filename>")
def download_file(filename):
    save_dir = r"C:\Users\10828991\OneDrive - LTIMindtree\Desktop\langgraph task"
    return send_from_directory(save_dir, filename, as_attachment=True)
