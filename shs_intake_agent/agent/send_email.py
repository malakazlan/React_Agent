import os
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv

def send_report_via_email(pdf_path: str, client_data: dict) -> bool:
    """
    Send the PDF report as an email attachment using SMTP.
    Returns True if sent successfully, False otherwise.
    """
    load_dotenv()
    smtp_email = os.getenv('SMTP_EMAIL')
    smtp_password = os.getenv('SMTP_PASSWORD') or os.getenv('APP_PASSWORD')
    email_to = os.getenv('EMAIL_TO')
    
    if not all([smtp_email, smtp_password, email_to]):
        print("[Email Error] Missing SMTP_EMAIL, SMTP_PASSWORD/APP_PASSWORD, or EMAIL_TO in .env")
        return False
    
    client_name = client_data.get('name', 'Unknown')
    eligible = client_data.get('eligible', False)
    score = client_data.get('eligibility_score', 'N/A')
    reasons = client_data.get('eligibility_reasons', [])
    
    subject = f"[SHS Intake] Eligibility Result for {client_name}"
    body = f"""
    SHS Intake Eligibility Result
    ----------------------------
    Client: {client_name}
    Eligible: {'YES' if eligible else 'NO'}
    Score: {score}
    Reasons:
    {chr(10).join(['- ' + r for r in reasons])}
    """
    
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = smtp_email
    msg['To'] = email_to
    msg.set_content(body)
    
    # Attach PDF
    try:
        with open(pdf_path, 'rb') as f:
            pdf_data = f.read()
        msg.add_attachment(pdf_data, maintype='application', subtype='pdf', filename=os.path.basename(pdf_path))
    except Exception as e:
        print(f"[Email Error] Could not attach PDF: {e}")
        return False
    
    # Send email
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(smtp_email, smtp_password)
            smtp.send_message(msg)
        print(f"[Email] Report sent to {email_to}")
        return True
    except Exception as e:
        print(f"[Email Error] {e}")
        return False 