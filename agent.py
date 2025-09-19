import os
import json
import logging
from typing import Any, Dict, List
from langgraph.checkpoint.memory import MemorySaver
from langchain.agents import create_react_agent, AgentExecutor, tool
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq
from dotenv import load_dotenv
from prompt import PENSION_AGENT_PROMPT


load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@tool
def get_pension_info(query: str) -> str:
    """
    Get information about NPF Pensions Ltd services and policies.
    
    Args:
        query: The user's question or request about pension services
        
    Returns:
        Detailed information about NPF Pensions services
    """
    
    if "faq" in query.lower() or "question" in query.lower():
        return """*Frequently Asked Questions:*

1. *How do I check my pension balance?*
    Visit our website at https://npfpensions.com.ng/ and log into your account.

2. *When can I withdraw my pension?*
    You can withdraw at retirement age (60 years) or in case of medical incapacity.

3. *How do I update my personal information?*
    Log into your account or visit any of our branches.

4. *What documents do I need for registration?*
    Valid ID, utility bill, and employment letter.

5. *How do I change my contribution amount?*
    Contact your employer or visit our website."""
    
    elif "calculator" in query.lower() or "calculate" in query.lower():
        return """**Pension Calculator:**

        To calculate your pension, I need the following information:
        - Your current age
        - Your expected retirement age
        - Your monthly contributions to the pension scheme
        - The number of years you've been contributing
        - Your current account balance (if known)

        Once I have this information, I can provide you with a personalized pension calculation."""
    
    elif "registration" in query.lower() or "register" in query.lower():
        return """*Registration Process:*

            To register with NPF Pensions Ltd:
            1. Visit our website at https://npfpensions.com.ng/
            2. Click on the "Register" button
            3. Fill out the registration form with your personal details
            4. Choose a username and password
            5. Verify your email address
            6. Upload required documents (ID, utility bill)
            7. Wait for account verification

            You can also visit any of our branches nationwide for in-person registration."""
    
    elif "company" in query.lower() or "about" in query.lower():
        return """*Company Information:*

        NPF Pensions Ltd is a leading Pension Fund Administrator (PFA) in Nigeria, licensed by the National Pension Commission (PenCom). We were incorporated on 21st October 2013 to cater to the unique needs of the Nigeria Police Force under the Contributory Pension Scheme (CPS). 

        Our goal is to effectively manage police personnel pensions, Group Life Assurance, and Health Insurance Schemes."""
    
    elif "services" in query.lower() or "service" in query.lower():
        return """*Services Offered:*

            1. Audited Accounts
            2. PenCom
            3. Fund Management
            4. Pension Calculator
            5. Whistle Blowing
            6. FAQ
            7. Customer Login

            *Our Services Include:*
            - Retirement Savings Account (RSA) management
            - Pension contribution processing
            - Retirement benefits calculation
            - Pension fund investment options
            - Pension transfer and rollover
            - Pension withdrawal and payment
            - General pension advice and guidance"""
    
    elif any(keyword in query.lower() for keyword in ["audited accounts", "audit", "1"]):
        return """*Audited Accounts:*

For detailed information about our audited accounts and financial reports, please visit our website at https://npfpensions.com.ng/ or contact us directly.

Our audited accounts provide transparency and accountability in managing your pension funds."""
    
    elif any(keyword in query.lower() for keyword in ["pencom", "2"]):
        return """*PenCom Information:*

NPF Pensions Ltd is licensed by the National Pension Commission (PenCom).

For specific PenCom-related information and compliance details, please visit our website at https://npfpensions.com.ng/ or contact us directly."""
            
    elif any(keyword in query.lower() for keyword in ["fund management", "management", "3"]):
        return """*Fund Management:*

We provide professional fund management services for your pension contributions.

For detailed information about our fund management strategies and performance, please visit our website at https://npfpensions.com.ng/ or contact us directly."""
    
    elif any(keyword in query.lower() for keyword in ["whistle blowing", "whistle", "5"]):
        return """*Whistle Blowing:*

We have a whistle blowing policy to ensure transparency and accountability.

For more information about our whistle blowing procedures, please visit our website at https://npfpensions.com.ng/ or contact us directly."""
    
    elif any(keyword in query.lower() for keyword in ["customer login", "login", "7"]):
        return """*Customer Login:*

You can access your pension account online through our secure customer portal.

To log into your account, please visit our website at https://npfpensions.com.ng/ and click on the "Customer Login" section."""
    
    else:
        return """I don't have specific information about that service at the moment.

            For more detailed information, please visit our website at https://npfpensions.com.ng/ or contact us directly.

            I can help you with these services:
            - FAQ (Frequently Asked Questions)
            - Pension Calculator
            - Registration Process
            - Company Information
            - Services Offered"""


def _chat_llm() -> ChatOpenAI:
    """Return a streaming chat model."""
    return ChatGroq(
        api_key=os.getenv("GROQ_API_KEY"),
        model="llama-3.3-70b-versatile", 
        temperature=0.3,
    )

class WhatsappAgent:
    """WhatsApp agent for NPF Pensions with memory and dynamic button support."""

    def __init__(self) -> None:
        self.memory = MemorySaver()
        self.llm = None
        self.agent = None
        self.policy_accepted = {}
        self.assistant_identity = {}

    async def initialize(self) -> None:
        """Initialize the agent."""
        try:
            logger.info("Initializing NPF Pensions Agent...")
            
            # Initialize the LLM
            self.llm = _chat_llm()
            
            # Create the ReAct agent with the pension info tool
            tools = [get_pension_info]
            agent = create_react_agent(
                self.llm,
                tools=tools,
                prompt=PromptTemplate(
                    template=PENSION_AGENT_PROMPT,
                    input_variables=["input", "agent_scratchpad", "tools", "tool_names"]
                )
            )
            
            # Create the agent executor
            self.agent = AgentExecutor(
                agent=agent,
                tools=tools,
                verbose=True,
                handle_parsing_errors=True,
                max_iterations=5,
                return_intermediate_steps=True
            )
            
            logger.info("NPF Pensions Agent initialized successfully")
        except Exception as e:
            logger.error(f"Agent initialization failed: {e}", exc_info=True)
            raise

    async def cleanup(self) -> None:
        """Cleanup resources."""
        logger.info("Cleaning up WhatsappAgent...")
        self.agent = None

    async def get_response(self, content: Any, thread_id: str) -> Dict[str, Any]:
        """
        Get a response from the agent with static images.
        Returns:
            A dictionary like {"text": "Your response.", "buttons": ["Button 1", "Button 2"], "avatar_data": "base64_image_data"}
        """
        try:
            user_input = content
            if "[name:" in content and "]" in content:
                try:
                    user_input = content.split("]", 1)[1].strip()
                    logger.info(f"Extracted user input: '{user_input}' from '{content}'")
                except:
                    user_input = content
            
            # Check if user input is just a number (service selection)
            is_number_only = user_input.strip().isdigit()
            
            # Preprocessing: Convert ALL numbers to service names to avoid tokenization issues
            number_to_service = {
                '1': 'audited accounts',
                '2': 'pencom',
                '3': 'fund management', 
                '4': 'pension calculator',
                '5': 'whistle blowing',
                '6': 'faq',
                '7': 'customer login'
            }
            
            original_content = content
            processed_content = user_input
            if user_input.strip() in number_to_service:
                processed_content = number_to_service[user_input.strip()]
                is_number_only = False
                logger.info(f"Converted number '{user_input}' to service '{processed_content}'")
            
            # Greeting detection - exclude numbers and service requests
            is_greeting = (not (user_input.strip().isdigit() and user_input.strip() in number_to_service)) and not any(service in processed_content.lower() for service in number_to_service.values()) and any(word in user_input.lower() for word in ['hi', 'hello', 'hey', 'good morning', 'good afternoon', 'good evening'])
            is_policy_acceptance = any(word in user_input.lower() for word in ['accept', 'accepted', 'agree', 'agreed', 'yes', 'ok', 'okay'])
            
            # Service request detection (check both original and converted content)
            is_service_request = (user_input.strip().isdigit() and user_input.strip() in number_to_service) or any(keyword in processed_content.lower() for keyword in ['audited', 'pencom', 'fund', 'calculator', 'whistle', 'faq', 'login', 'services', 'registration', 'company'])
            
            has_accepted_policy = self.policy_accepted.get(thread_id, False)
            
            # Update policy acceptance status
            if is_policy_acceptance:
                self.policy_accepted[thread_id] = True
                has_accepted_policy = True
                logger.info(f"Policy accepted for user {thread_id}")
                # Return service list immediately after policy acceptance
                if thread_id not in self.assistant_identity:
                    _, assistant_name = self._get_static_image_base64()
                    self.assistant_identity[thread_id] = assistant_name
                else:
                    assistant_name = self.assistant_identity[thread_id]
                
                image_data = self._get_image_for_identity(assistant_name)
                return {
                    "text": f"Thank you for accepting our privacy policy! Here are the services I can help you with:\n\n1. Audited Accounts\n2. PenCom\n3. Fund Management\n4. Pension Calculator\n5. Whistle Blowing\n6. FAQ\n7. Customer Login\n\nPlease select a service by typing the number (e.g., '4') or the service name (e.g., 'Pension Calculator' or 'FAQ').",
                    "buttons": [],
                    "avatar_data": image_data
                }
            
            # Handle service requests based on policy status
            if is_service_request:
                if has_accepted_policy:
                    # Policy accepted - provide service directly
                    logger.info(f"Service request with accepted policy: {user_input} -> {processed_content}")
                    try:
                        tool_result = get_pension_info(processed_content)
                        
                        # Get or assign assistant identity
                        if thread_id not in self.assistant_identity:
                            _, assistant_name = self._get_static_image_base64()
                            self.assistant_identity[thread_id] = assistant_name
                        else:
                            assistant_name = self.assistant_identity[thread_id]
                        
                        image_data = self._get_image_for_identity(assistant_name)
                        text_response = tool_result.replace("Toni", assistant_name)
                        
                        return {"text": text_response, "buttons": [], "avatar_data": image_data}
                    except Exception as e:
                        logger.error(f"Service execution error: {e}")
                        return {
                            "text": "I'm having trouble processing your request. Please try again or visit our website at https://npfpensions.com.ng/",
                            "buttons": [],
                            "avatar_data": None
                        }
                else:
                    # Service request but no policy - show policy first
                    logger.info(f"Service request without policy acceptance: {original_content}")
                    if thread_id not in self.assistant_identity:
                        _, assistant_name = self._get_static_image_base64()
                        self.assistant_identity[thread_id] = assistant_name
                    else:
                        assistant_name = self.assistant_identity[thread_id]
                    
                    image_data = self._get_image_for_identity(assistant_name)
                    return {
                        "text": f"Hello! I am {assistant_name}, your personal virtual assistant for NPF Pensions Ltd. I'm here to help you with information about our pension services, calculations, account access, and more.\n\nBefore we proceed, please review and accept our terms and conditions. You can find the details here: https://npfpensions.com.ng/privacy-policy/",
                        "buttons": ["Accept Policy", "Decline Policy"],
                        "avatar_data": image_data
                    }
            
            # Handle greetings
            if is_greeting:
                logger.info(f"Greeting detected: {original_content}")
                if thread_id not in self.assistant_identity:
                    _, assistant_name = self._get_static_image_base64()
                    self.assistant_identity[thread_id] = assistant_name
                else:
                    assistant_name = self.assistant_identity[thread_id]
                
                image_data = self._get_image_for_identity(assistant_name)
                
                # Extract user name from content if available
                user_name = ""
                if "[name:" in content:
                    try:
                        user_name = content.split("[name:")[1].split("]")[0] + "! "
                    except:
                        user_name = ""
                
                return {
                    "text": f"Hello, {user_name}I am {assistant_name}, your personal virtual assistant for NPF Pensions Ltd. I'm here to help you with information about our pension services, calculations, account access, and more.\n\nBefore we proceed, please review and accept our terms and conditions. You can find the details here: https://npfpensions.com.ng/privacy-policy/",
                    "buttons": ["Accept Policy", "Decline Policy"],
                    "avatar_data": image_data
                }
            
            # Use LangChain ReAct agent for other cases
            if not self.agent:
                logger.error("Agent not initialized")
                return {
                    "text": "I'm currently unavailable. Please try again later.",
                    "buttons": [],
                    "avatar_data": None
                }
            
            # Prepare input for the ReAct agent
            agent_input = {
                "input": content,
                "agent_scratchpad": []
            }
            
            # Get response from ReAct agent
            response = await self.agent.ainvoke(agent_input)
            
            # Extract the final answer from the response
            if isinstance(response, dict) and 'output' in response and 'intermediate_steps' in response:
                # Check if output indicates iteration limit but we have tool results
                if "iteration limit" in response['output'].lower() or "time limit" in response['output'].lower():
                    # Use intermediate steps instead
                    intermediate_steps = response.get('intermediate_steps', [])
                    if intermediate_steps:
                        # Get the tool result from the first step
                        first_step = intermediate_steps[0]
                        if len(first_step) > 1:
                            tool_result = first_step[1]  # Second element is the tool result
                            raw_response = f"Final Answer: {tool_result}"
                        else:
                            raw_response = response['output']
                    else:
                        raw_response = response['output']
                else:
                    raw_response = response['output']
            elif isinstance(response, dict) and 'output' in response:
                raw_response = response['output']
            elif isinstance(response, dict) and 'intermediate_steps' in response:
                # If we have intermediate steps but no final output, extract from the first successful tool call
                intermediate_steps = response.get('intermediate_steps', [])
                if intermediate_steps:
                    # Get the tool result from the first step (avoid repetition)
                    first_step = intermediate_steps[0]
                    if len(first_step) > 1:
                        tool_result = first_step[1]
                        raw_response = f"Final Answer: {tool_result}"
                    else:
                        raw_response = str(response)
                else:
                    raw_response = str(response)
            else:
                raw_response = str(response)
            
            # Extract only the Final Answer from ReAct format
            text_response = self._extract_final_answer(raw_response)
            
            # Get or assign assistant identity for this user
            if thread_id not in self.assistant_identity:
                # First time for this user - randomly select identity
                _, assistant_name = self._get_static_image_base64()
                self.assistant_identity[thread_id] = assistant_name
                logger.info(f"Assigned identity '{assistant_name}' to user {thread_id}")
            else:
                # Use existing identity for this user
                assistant_name = self.assistant_identity[thread_id]
                logger.info(f"Using existing identity '{assistant_name}' for user {thread_id}")
            
            # Get the corresponding image for the assigned identity
            image_data = self._get_image_for_identity(assistant_name)
            
            # Parse buttons from the response
            buttons = []
            button_line = ""
            if "__BUTTONS__" in text_response:
                text_response, button_line = text_response.split("__BUTTONS__", 1)
                text_response = text_response.strip()
                # Split buttons by comma and strip whitespace
                buttons = [b.strip() for b in button_line.split(",") if b.strip()]
            elif "**BUTTONS**" in text_response:
                text_response, button_line = text_response.split("**BUTTONS**", 1)
                text_response = text_response.strip()
                # Split buttons by comma and strip whitespace
                buttons = [b.strip() for b in button_line.split(",") if b.strip()]
            elif "## BUTTONS ##" in text_response:
                text_response, button_line = text_response.split("## BUTTONS ##", 1)
                text_response = text_response.strip()
                # Split buttons by comma and strip whitespace
                buttons = [b.strip() for b in button_line.split(",") if b.strip()]

            if not text_response:
                text_response = "I've processed that. How else can I assist you?"
            
            # Replace "Toni" with the dynamic name in the response
            text_response = text_response.replace("Toni", assistant_name)
            
            logger.info(f"Agent final output: TEXT='{text_response}', BUTTONS={buttons}, AVATAR_DATA={'Present' if image_data else 'None'}")
            return {"text": text_response, "buttons": buttons, "avatar_data": image_data}
                
        except Exception as e:
            logger.error(f"Error getting agent response: {e}")
            # Fallback response
            return {
                "text": "I apologize, but I'm having trouble processing your request. Please try again.",
                "buttons": [],
                "avatar_data": None
            }
    
    def _extract_final_answer(self, raw_response: str) -> str:
        """Extract the response content, cleaning up any formatting."""
        try:
            # Look for "Final Answer:" in the response
            if "Final Answer:" in raw_response:
                # Split by "Final Answer:" and take everything after it
                parts = raw_response.split("Final Answer:", 1)
                if len(parts) > 1:
                    return parts[1].strip()
            
            # If no "Final Answer:" found, return the raw response as is
            return raw_response.strip()
            
        except Exception as e:
            logger.warning(f"Error extracting final answer: {e}")
            return raw_response
    
    def reset_policy_acceptance(self, thread_id: str) -> None:
        """Reset policy acceptance for a specific user."""
        if thread_id in self.policy_accepted:
            del self.policy_accepted[thread_id]
            logger.info(f"Policy acceptance reset for user {thread_id}")
    
    def reset_user_session(self, thread_id: str) -> None:
        """Reset policy acceptance and assistant identity for a user."""
        self.reset_policy_acceptance(thread_id)
        if thread_id in self.assistant_identity:
            del self.assistant_identity[thread_id]
            logger.info(f"Assistant identity reset for user {thread_id}")
        logger.info(f"Complete session reset for user {thread_id}")

    def _get_image_for_identity(self, identity: str) -> str:
        """Get the base64 image for a specific identity (Toni or Debby)."""
        try:
            import base64
            import os
            
            # Image paths for each identity
            image_paths = {
                "Toni": r"C:\Users\hp\Downloads\NPFPension\whatsapp-agent\ChatGPT Image Sep 18, 2025, 05_25_19 PM.png",
                "Debby": r"C:\Users\hp\Downloads\NPFPension\whatsapp-agent\ChatGPT Image Sep 18, 2025, 05_25_41 PM.png"
            }
            
            image_path = image_paths.get(identity, image_paths["Toni"])  # Default to Toni
            
            if os.path.exists(image_path):
                with open(image_path, "rb") as image_file:
                    image_data = image_file.read()
                    base64_image = base64.b64encode(image_data).decode('utf-8')
                    logger.info(f"Loaded {identity} image from {os.path.basename(image_path)}, size: {len(image_data)} bytes")
                    return base64_image
            else:
                logger.warning(f"Image file not found for {identity}: {image_path}")
                # Fallback to placeholder
                return "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
                
        except Exception as e:
            logger.error(f"Error loading image for {identity}: {e}")
            # Fallback to placeholder
            return "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="

    def _get_static_image_base64(self) -> tuple[str, str]:
        """Return a randomly selected base64 encoded image and corresponding name for every response."""
        try:
            import base64
            import os
            import random
            
            # Image paths with corresponding names
            image_data = [
                {
                    "path": r"C:\Users\hp\Downloads\NPFPension\whatsapp-agent\ChatGPT Image Sep 18, 2025, 05_25_41 PM.png",
                    "name": "Debby"
                },
                {
                    "path": r"C:\Users\hp\Downloads\NPFPension\whatsapp-agent\ChatGPT Image Sep 18, 2025, 05_25_19 PM.png", 
                    "name": "Toni"
                }
            ]
            
            # Randomly select an image
            selected = random.choice(image_data)
            
            if os.path.exists(selected["path"]):
                with open(selected["path"], "rb") as image_file:
                    image_data_bytes = image_file.read()
                    base64_image = base64.b64encode(image_data_bytes).decode('utf-8')
                    logger.info(f"Loaded {selected['name']} image from {os.path.basename(selected['path'])}, size: {len(image_data_bytes)} bytes")
                    return base64_image, selected["name"]
            else:
                logger.warning(f"Selected image file not found: {selected['path']}")
                for fallback in image_data:
                    if os.path.exists(fallback["path"]):
                        with open(fallback["path"], "rb") as image_file:
                            image_data_bytes = image_file.read()
                            base64_image = base64.b64encode(image_data_bytes).decode('utf-8')
                            logger.info(f"Using fallback {fallback['name']} image from {os.path.basename(fallback['path'])}, size: {len(image_data_bytes)} bytes")
                            return base64_image, fallback["name"]
                
                # Final fallback to placeholder
                return "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==", "Toni"
                
        except Exception as e:
            logger.error(f"Error loading random image: {e}")
            # Fallback to placeholder
            return "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==", "Toni"