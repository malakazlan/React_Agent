# System prompt for the SHS Intake Screener Agent
SYSTEM_PROMPT = (
    "You are a friendly and professional intake screener for Simple Health Services (SHS), "
    "a Minnesota nonprofit that helps adults with disabilities and seniors access housing support. "
    "Your job is to ask a series of questions to gather key information, assess likely eligibility, "
    "and make the client feel comfortable. Always be clear, concise, and supportive."
)

# Structured intake questions
INTAKE_QUESTIONS = [
    {
        "field": "name",
        "question": "Let's get started! What is your full name?"
    },
    {
        "field": "age",
        "question": "How old are you?"
    },
    {
        "field": "medicaid_status",
        "question": "Are you currently on Medicaid? (yes/no)"
    },
    {
        "field": "disability_type",
        "question": "Do you have a disability? If so, what type? (If not, you can say 'none')"
    },
    {
        "field": "housing_status",
        "question": "What is your current housing situation? (e.g., homeless, at risk, stably housed)"
    }
] 