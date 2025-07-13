import gradio as gr
import os
import json
from datetime import datetime
from agent.intake_chain import create_shs_react_agent, reset_conversation_state, PREBUILT_DATA

# Set API key
os.environ["GOOGLE_API_KEY"] = "AIzaSyBHkbWsAShyXwqtXDnOv1-p8Azfv7HC6Bs"

# Global variables
agent_executor = None
conversation_history = []

def initialize_agent():
    """Initialize the ReAct agent"""
    global agent_executor
    if agent_executor is None:
        agent_executor = create_shs_react_agent()
    reset_conversation_state()
    return "🤖 SHS ReAct Agent initialized and ready!"

def process_message(message, history):
    """Process user message and return agent response"""
    global agent_executor, conversation_history
    
    if agent_executor is None:
        agent_executor = create_shs_react_agent()
    
    try:
        # Add user message to history
        conversation_history.append({"role": "user", "content": message, "timestamp": datetime.now().strftime("%H:%M:%S")})
        
        # Process with agent
        response = agent_executor.invoke({'input': message})
        
        # Add agent response to history
        conversation_history.append({"role": "assistant", "content": response['output'], "timestamp": datetime.now().strftime("%H:%M:%S")})
        
        return response['output']
        
    except Exception as e:
        error_msg = f"Error: {str(e)}"
        conversation_history.append({"role": "assistant", "content": error_msg, "timestamp": datetime.now().strftime("%H:%M:%S")})
        return error_msg

def use_prebuilt_data(client_key):
    """Use prebuilt test data"""
    if client_key not in PREBUILT_DATA:
        return f"Pre-built client '{client_key}' not found. Available: {list(PREBUILT_DATA.keys())}"
    
    message = f"Use prebuilt data for {client_key}"
    return process_message(message, [])

def get_conversation_summary():
    """Get a summary of the conversation"""
    if not conversation_history:
        return "No conversation history yet."
    
    summary = "📋 **Conversation Summary:**\n\n"
    for entry in conversation_history:
        role_icon = "👤" if entry["role"] == "user" else "🤖"
        summary += f"{role_icon} **{entry['role'].title()}** ({entry['timestamp']}):\n{entry['content']}\n\n"
    
    return summary

def clear_conversation():
    """Clear conversation history"""
    global conversation_history
    conversation_history = []
    reset_conversation_state()
    return "Conversation cleared!"

def get_available_commands():
    """Get list of available commands"""
    commands = """
🎯 **Available Commands:**

**Data Collection:**
• "Collect client name: [name]"
• "Collect client age: [age]"
• "Collect Medicaid status: [yes/no]"
• "Collect disability type: [type]"
• "Collect housing status: [status]"

**Assessment & Actions:**
• "Assess eligibility"
• "Send data to webhook"
• "Get next question"

**Testing:**
• "Use prebuilt data for test_client_1"
• "Use prebuilt data for test_client_2"

**Natural Language:**
• "Start intake for [name], age [age], with [details]"
• "What information do you need?"
• "Show me the assessment results"
    """
    return commands

# Custom CSS for better styling
custom_css = """
.gradio-container {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}

.chat-message {
    padding: 15px;
    margin: 10px 0;
    border-radius: 10px;
    border-left: 4px solid #007bff;
}

.user-message {
    background-color: #f8f9fa;
    border-left-color: #28a745;
}

.assistant-message {
    background-color: #e3f2fd;
    border-left-color: #007bff;
}

.tool-usage {
    background-color: #fff3cd;
    border: 1px solid #ffeaa7;
    border-radius: 5px;
    padding: 10px;
    margin: 5px 0;
    font-size: 0.9em;
    color: #856404;
}

.eligibility-result {
    background-color: #d4edda;
    border: 1px solid #c3e6cb;
    border-radius: 5px;
    padding: 15px;
    margin: 10px 0;
}

.eligibility-result.eligible {
    background-color: #d1ecf1;
    border-color: #bee5eb;
}

.eligibility-result.not-eligible {
    background-color: #f8d7da;
    border-color: #f5c6cb;
}
"""

# Create the Gradio interface
with gr.Blocks(css=custom_css, title="SHS ReAct Intake Agent", theme=gr.themes.Soft()) as demo:
    
    gr.Markdown("""
    # 🏥 SHS ReAct Intake Agent
    ### Simple Health Services - Housing Stabilization Services Intake
    
    This intelligent agent uses ReAct (Reasoning and Acting) pattern to conduct intake assessments for housing support services.
    """)
    
    with gr.Row():
        with gr.Column(scale=2):
            # Main chat interface
            chatbot = gr.Chatbot(
                label="Conversation",
                height=500,
                show_label=True,
                container=True,
                type="messages"
            )
            
            with gr.Row():
                msg = gr.Textbox(
                    label="Your Message",
                    placeholder="Type your message here...",
                    scale=4
                )
                send_btn = gr.Button("Send", variant="primary", scale=1)
            
            with gr.Row():
                clear_btn = gr.Button("Clear Conversation", variant="secondary")
                init_btn = gr.Button("Initialize Agent", variant="secondary")
        
        with gr.Column(scale=1):
            # Sidebar with controls and info
            gr.Markdown("### 🎛️ Quick Actions")
            
            with gr.Group():
                gr.Markdown("**Test with Pre-built Data:**")
                prebuilt_btn1 = gr.Button("Test Client 1 (Eligible)", size="sm")
                prebuilt_btn2 = gr.Button("Test Client 2 (Not Eligible)", size="sm")
            
            with gr.Group():
                gr.Markdown("**Common Commands:**")
                quick_commands = [
                    "What is the next question I should ask?",
                    "Assess eligibility",
                    "Send data to webhook",
                    "Show me the assessment results"
                ]
                
                for cmd in quick_commands:
                    btn = gr.Button(cmd, size="sm", variant="outline")
                    btn.click(
                        lambda c=cmd: process_message(c, []),
                        outputs=[chatbot]
                    )
            
            with gr.Group():
                gr.Markdown("### 📊 Information")
                summary_btn = gr.Button("Show Conversation Summary", size="sm")
                commands_btn = gr.Button("Show Available Commands", size="sm")
                
                summary_output = gr.Textbox(
                    label="Summary",
                    lines=10,
                    interactive=False
                )
    
    # Event handlers
    def user_input(user_message, history):
        if user_message.strip() == "":
            return history, ""
        
        bot_message = process_message(user_message, history)
        history.append((user_message, bot_message))
        return history, ""
    
    # Main chat functionality
    msg.submit(
        user_input,
        inputs=[msg, chatbot],
        outputs=[chatbot, msg]
    )
    
    send_btn.click(
        user_input,
        inputs=[msg, chatbot],
        outputs=[chatbot, msg]
    )
    
    # Clear conversation
    clear_btn.click(
        clear_conversation,
        outputs=[chatbot]
    )
    
    # Initialize agent
    init_btn.click(
        initialize_agent,
        outputs=[chatbot]
    )
    
    # Prebuilt data buttons
    prebuilt_btn1.click(
        lambda: use_prebuilt_data("test_client_1"),
        outputs=[chatbot]
    )
    
    prebuilt_btn2.click(
        lambda: use_prebuilt_data("test_client_2"),
        outputs=[chatbot]
    )
    
    # Summary and commands
    summary_btn.click(
        get_conversation_summary,
        outputs=[summary_output]
    )
    
    commands_btn.click(
        get_available_commands,
        outputs=[summary_output]
    )
    
    # Footer
    gr.Markdown("""
    ---
    **SHS ReAct Intake Agent v2.0** | Built with LangChain, Google Gemini, and Gradio
    
    This agent helps assess eligibility for Housing Stabilization Services by collecting client information
    and making intelligent decisions using the ReAct pattern.
    """)

if __name__ == "__main__":
    demo.launch(
        server_name="127.0.0.1",
        server_port=7860,
        share=False,
        debug=True
    ) 