import streamlit as st
import os
from datetime import datetime
from agent.intake_chain import create_shs_react_agent, reset_conversation_state, PREBUILT_DATA
from agent.generate_report import generate_pdf_report
from agent.send_email import send_report_via_email

# Set API key
os.environ["GOOGLE_API_KEY"] = "AIzaSyAEQdT0r_YOngC7Cb2N3w6AccY2KWKL470"

st.set_page_config(page_title="SHS ReAct Intake Agent", layout="wide")
st.title("🏥 SHS ReAct Intake Agent")
st.markdown("""
**Simple Health Services - Housing Stabilization Services Intake**

This intelligent agent uses ReAct (Reasoning and Acting) pattern to conduct intake assessments for housing support services.
""")

# Session state
if 'agent_executor' not in st.session_state:
    st.session_state.agent_executor = create_shs_react_agent()
    st.session_state.conversation = []
    st.session_state.last_client_data = None
    st.session_state.status = ""
    reset_conversation_state()

# Sidebar
with st.sidebar:
    st.header("Quick Actions")
    if st.button("Test Client 1 (Eligible)"):
        msg = "Use prebuilt data for test_client_1"
        response = st.session_state.agent_executor.invoke({'input': msg})
        st.session_state.conversation.append(("You", msg))
        st.session_state.conversation.append(("Agent", response['output']))
    if st.button("Test Client 2 (Not Eligible)"):
        msg = "Use prebuilt data for test_client_2"
        response = st.session_state.agent_executor.invoke({'input': msg})
        st.session_state.conversation.append(("You", msg))
        st.session_state.conversation.append(("Agent", response['output']))
    if st.button("Clear Conversation"):
        st.session_state.conversation = []
        st.session_state.last_client_data = None
        st.session_state.status = ""
        reset_conversation_state()
        st.success("Conversation cleared!")
    st.markdown("---")
    st.markdown("**Common Commands:**")
    st.markdown("- What is the next question I should ask?\n- Assess eligibility\n- Show me the assessment results")
    st.markdown("---")
    st.markdown("**Available Natural Language:**\n- Start intake for [name], age [age], with [details]\n- What information do you need?\n- Show me the assessment results")

# Main chat area
st.subheader("Conversation")
chat_placeholder = st.empty()

# Input box
user_input = st.text_input("Type your message and press Enter", "", key="user_input")

if user_input:
    st.session_state.conversation.append(("You", user_input))
    with st.spinner("Agent is thinking..."):
        response = st.session_state.agent_executor.invoke({'input': user_input})
        st.session_state.conversation.append(("Agent", response['output']))
        # Try to extract client data from the agent's state if available
        try:
            from agent.intake_chain import conversation_state
            if conversation_state.get('answers', {}).get('eligible') is not None:
                st.session_state.last_client_data = conversation_state['answers'].copy()
        except Exception:
            pass
    st.experimental_rerun()

# Display conversation
for role, msg in st.session_state.conversation:
    if role == "You":
        st.markdown(f"<div style='background:#f8f9fa;padding:10px;border-radius:8px;margin-bottom:4px'><b>👤 You:</b> {msg}</div>", unsafe_allow_html=True)
    else:
        # Highlight eligibility and email status if present
        highlight = ""
        if "Eligible:" in msg or "Report generated" in msg or "emailed" in msg:
            highlight = "background:#e3f2fd;"
        st.markdown(f"<div style='{highlight}padding:10px;border-radius:8px;margin-bottom:4px'><b>🤖 Agent:</b> {msg}</div>", unsafe_allow_html=True)

# Show eligibility, PDF, and email status if available
def show_status():
    if st.session_state.last_client_data:
        data = st.session_state.last_client_data
        st.markdown("---")
        st.subheader("Eligibility Assessment Result")
        st.markdown(f"**Name:** {data.get('name','N/A')}  ")
        st.markdown(f"**Age:** {data.get('age','N/A')}  ")
        st.markdown(f"**Medicaid Status:** {data.get('medicaid_status','N/A')}  ")
        st.markdown(f"**Disability Type:** {data.get('disability_type','N/A')}  ")
        st.markdown(f"**Housing Status:** {data.get('housing_status','N/A')}  ")
        st.markdown(f"**Eligible:** {'✅ YES' if data.get('eligible') else '❌ NO'}  ")
        st.markdown(f"**Eligibility Score:** {data.get('eligibility_score','N/A')}  ")
        st.markdown("**Reasons:**")
        for reason in data.get('eligibility_reasons', []):
            st.markdown(f"- {reason}")
        # Show PDF download link if report exists
        import glob
        import os
        client_name = data.get('name', 'Unknown').replace(' ', '_')
        pdfs = sorted(glob.glob(os.path.join(os.path.dirname(__file__), 'results', f'eligibility_report_{client_name}_*.pdf')), reverse=True)
        if pdfs:
            with open(pdfs[0], "rb") as f:
                st.download_button("Download Eligibility Report (PDF)", f, file_name=os.path.basename(pdfs[0]), mime="application/pdf")
        st.markdown("---")

show_status() 