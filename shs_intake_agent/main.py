import os
os.environ["GOOGLE_API_KEY"] = "Your geimini api here "
from agent.intake_chain import create_shs_react_agent, reset_conversation_state, PREBUILT_DATA
from agent.generate_report import generate_pdf_report
from agent.send_email import send_report_via_email
from dotenv import load_dotenv

load_dotenv()

def main():
    print("SHS ReAct Intake Agent")
    print("=" * 50)
    print("This agent uses ReAct (Reasoning and Acting) pattern with tools.")
    print("You can interact with it using natural language commands.\n")
    
    # Create the ReAct agent
    agent_executor = create_shs_react_agent()
    
    # Example commands
    print("Example commands you can try:")
    print("1. 'Start a new intake for John Smith, age 45, with Medicaid, physical disability, at risk of homelessness'")
    print("2. 'Use prebuilt data for test_client_1'")
    print("3. 'Collect information: name is Sarah Wilson, age 42, has Medicaid, mobility disability, at risk of homelessness'")
    print("4. 'Assess eligibility and generate report and email'")
    print("5. 'What is the next question I should ask?'")
    print("\nType 'quit' to exit.\n")
    
    last_client_data = None
    while True:
        try:
            # Get user input
            user_input = input("You: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
            
            if not user_input:
                continue
            
            print("\n🔄 Processing...")
            
            # Special command for report and email
            if 'generate report and email' in user_input.lower():
                if last_client_data is None:
                    print("No eligibility data available. Please assess eligibility first.")
                    continue
                pdf_path = generate_pdf_report(last_client_data)
                print(f"PDF report generated: {pdf_path}")
                sent = send_report_via_email(pdf_path, last_client_data)
                if sent:
                    print("Email sent successfully!")
                else:
                    print("Failed to send email.")
                continue
            
            # Execute the agent
            response = agent_executor.invoke({'input': user_input})
            print(f"\n Agent: {response['output']}")
            # Try to extract client data from the agent's state if available
            # (Assume agent exposes conversation_state for now)
            try:
                from agent.intake_chain import conversation_state
                if conversation_state.get('answers', {}).get('eligible') is not None:
                    last_client_data = conversation_state['answers'].copy()
            except Exception:
                pass
            print("\n" + "-" * 50)
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f" Error: {e}")
            print("Try rephrasing your request or type 'quit' to exit.")

if __name__ == "__main__":
    main() 