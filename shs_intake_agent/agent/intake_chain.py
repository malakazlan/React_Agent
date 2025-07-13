import os
os.environ["GOOGLE_API_KEY"] = "your actual api here"
from dotenv import load_dotenv
load_dotenv()

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.tools import tool
from langchain.agents import create_react_agent, AgentExecutor
from langchain import hub
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import PydanticOutputParser
from .intake_prompt import SYSTEM_PROMPT, INTAKE_QUESTIONS
from .output_schema import IntakeData
import json
import re
from agent.generate_report import generate_pdf_report
from agent.send_email import send_report_via_email

# Initialize the model
model = ChatGoogleGenerativeAI(
    model="models/gemini-2.0-flash-001",

    temperature=0.3,
)

# Pre-built test data
PREBUILT_DATA = {
    "test_client_1": {
        "name": "John Smith",
        "age": 45,
        "medicaid_status": True,
        "disability_type": "Physical disability",
        "housing_status": "At risk of homelessness",
        "eligible": True
    },
    "test_client_2": {
        "name": "Mary Johnson",
        "age": 28,
        "medicaid_status": False,
        "disability_type": "None",
        "housing_status": "Stably housed",
        "eligible": False
    }
}

# Global state for conversation
conversation_state = {
    "answers": {},
    "current_question": 0,
    "conversation_complete": False
}

@tool
def collect_client_name(name: str) -> str:
    """
    Collect and validate the client's full name
    """
    if not name or not name.strip():
        return "Please provide a valid full name."
    
    conversation_state["answers"]["name"] = name.strip()
    return f"Name collected: {name.strip()}"

@tool
def collect_client_age(age: str) -> str:
    """
    Collect and validate the client's age
    """
    try:
        age_int = int(age)
        if age_int < 0 or age_int > 120:
            return "Please provide a valid age between 0 and 120."
        
        conversation_state["answers"]["age"] = age_int
        return f"Age collected: {age_int}"
    except ValueError:
        return "Please provide a valid numeric age."

@tool
def collect_medicaid_status(has_medicaid: str) -> str:
    """
    Collect information about client's Medicaid status
    """
    has_medicaid_lower = has_medicaid.lower().strip()
    if has_medicaid_lower in ["yes", "y", "true", "1"]:
        conversation_state["answers"]["medicaid_status"] = True
        return "Medicaid status: Yes"
    elif has_medicaid_lower in ["no", "n", "false", "0"]:
        conversation_state["answers"]["medicaid_status"] = False
        return "Medicaid status: No"
    else:
        return "Please answer with 'yes' or 'no' for Medicaid status."

@tool
def collect_disability_type(disability: str) -> str:
    """
    Collect information about client's disability type
    """
    if not disability or not disability.strip():
        conversation_state["answers"]["disability_type"] = "None"
        return "Disability type: None"
    
    conversation_state["answers"]["disability_type"] = disability.strip()
    return f"Disability type collected: {disability.strip()}"

@tool
def collect_housing_status(housing: str) -> str:
    """
    Collect information about client's current housing status
    """
    if not housing or not housing.strip():
        return "Please describe your current housing situation."
    
    conversation_state["answers"]["housing_status"] = housing.strip()
    return f"Housing status collected: {housing.strip()}"

@tool
def assess_eligibility() -> str:
    """
    Assess client eligibility for SHS Housing Stabilization Services based on collected information.
    If assessment is complete, automatically generate a PDF report and send it via email.
    """
    data = conversation_state["answers"]
    
    if len(data) < 5:
        return "Cannot assess eligibility yet. Need to collect all required information first."
    
    score = 0
    reasons = []
    
    # Age criteria (adults with disabilities or seniors)
    if data.get('age', 0) >= 18:
        score += 1
        reasons.append("Adult age requirement met")
    
    # Medicaid status (preferred but not always required)
    if data.get('medicaid_status', False):
        score += 2
        reasons.append("Medicaid eligible")
    
    # Disability status
    disability = data.get('disability_type', '').lower()
    if disability and disability != 'none':
        score += 2
        reasons.append(f"Has disability: {disability}")
    
    # Housing status (priority for those at risk or homeless)
    housing = data.get('housing_status', '').lower()
    if 'homeless' in housing or 'at risk' in housing:
        score += 3
        reasons.append("Housing instability identified")
    elif 'stably' in housing:
        score += 1
        reasons.append("Currently stably housed")
    
    # Decision threshold
    eligible = score >= 3
    data['eligible'] = eligible
    data['eligibility_score'] = score
    data['eligibility_reasons'] = reasons
    
    conversation_state["conversation_complete"] = True
    
    # Automatically generate report and send email if not already done
    if not data.get('report_generated'):
        pdf_path = generate_pdf_report(data)
        data['report_generated'] = True
        email_sent = send_report_via_email(pdf_path, data)
        if email_sent:
            email_status = "Report generated and emailed to staff."
        else:
            email_status = "Report generated, but failed to send email."
    else:
        email_status = "Report already generated and email attempted."
    
    result = {
        "eligible": eligible,
        "score": score,
        "reasons": reasons,
        "client_data": data
    }
    
    return f"Eligibility Assessment Complete:\nEligible: {eligible}\nScore: {score}\nReasons: {', '.join(reasons)}\n{email_status}"

@tool
def get_next_question() -> str:
    """
    Get the next question to ask the client based on what information is still needed
    """
    questions = INTAKE_QUESTIONS
    answers = conversation_state["answers"]
    
    for q in questions:
        if q["field"] not in answers:
            return f"Next question: {q['question']}"
    
    return "All questions have been answered. Ready to assess eligibility."

@tool
def use_prebuilt_data(client_key: str) -> str:
    """
    Use pre-built test data for demonstration purposes
    """
    if client_key not in PREBUILT_DATA:
        return f"Pre-built client '{client_key}' not found. Available: {list(PREBUILT_DATA.keys())}"
    
    conversation_state["answers"] = PREBUILT_DATA[client_key].copy()
    conversation_state["conversation_complete"] = True
    
    return f"Loaded pre-built data for {client_key}: {PREBUILT_DATA[client_key]['name']}"

def create_shs_react_agent():
    """
    Create the SHS ReAct agent with all tools
    """
    # Get the ReAct prompt from hub
    prompt = hub.pull('hwchase17/react')
    
    # Create the agent
    agent = create_react_agent(
        llm=model,
        tools=[
            collect_client_name,
            collect_client_age,
            collect_medicaid_status,
            collect_disability_type,
            collect_housing_status,
            assess_eligibility,
            get_next_question,
            use_prebuilt_data
        ],
        prompt=prompt
    )
    
    # Create the agent executor
    agent_executor = AgentExecutor(
        agent=agent,
        tools=[
            collect_client_name,
            collect_client_age,
            collect_medicaid_status,
            collect_disability_type,
            collect_housing_status,
            assess_eligibility,
            get_next_question,
            use_prebuilt_data
        ],
        verbose=True,
        max_iterations=20
    )
    
    return agent_executor

def reset_conversation_state():
    """
    Reset the conversation state for a new intake
    """
    global conversation_state
    conversation_state = {
        "answers": {},
        "current_question": 0,
        "conversation_complete": False
    } 