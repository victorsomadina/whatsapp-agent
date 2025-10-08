import os
import json
import logging
from typing import Any, Dict, List
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from langchain.agents import tool
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
        Detailed information about NPF Pensions services or an instruction to the agent if info is not found.
    """
    
    if "faq" in query.lower() or "question" in query.lower() or "6" in query:
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
    
    elif "calculator" in query.lower() or "calculate" in query.lower() or "4" in query:
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
        return "No specific pre-written information found for this query. Use your general knowledge about the Nigerian pension industry to provide a helpful answer."


def _chat_llm() -> ChatGroq:
    """Return a streaming chat model."""
    return ChatGroq(
        api_key=os.getenv("GROQ_API_KEY"),
        model="meta-llama/llama-4-scout-17b-16e-instruct", 
        temperature=0.1,
    )

class WhatsappAgent:
    """WhatsApp agent for NPF Pensions with memory and dynamic button support."""

    def __init__(self) -> None:
        self.memory = MemorySaver()
        self.llm = _chat_llm()
        self.agent = None
        self.policy_accepted = {}
        self.assistant_identity = {}

    async def initialize(self) -> None:
        """Initialize the agent."""
        try:
            logger.info("Initializing NPF Pensions Agent...")
            
            tools = [get_pension_info]
            
            # The agent is created with langgraph.prebuilt
            self.agent = create_react_agent(
                model=self.llm,
                tools=tools,
                prompt=PENSION_AGENT_PROMPT,
                checkpointer=self.memory,
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
        Get a response from the agent.
        Returns: A dictionary like {"text": str | None, "buttons": List | None, "list": Dict | None, "avatar_data": str | None}
        Parses DSL for __LIST__ and __BUTTONS__ from the LLM response.
        """
        try:
            user_input = content
            if "[name:" in content and "]" in content:
                try:
                    user_input = content.split("]", 1)[1].strip()
                    logger.info(f"Extracted user input: '{user_input}' from '{content}'")
                except:
                    user_input = content

            # Handle main menu request (type "0") - let LLM generate __LIST__ format
            if user_input.strip() == '0':
                logger.info(f"User {thread_id} requested main menu.")
                has_accepted_policy = self.policy_accepted.get(thread_id, False)
                if has_accepted_policy:
                    # Let the LLM handle the main menu generation with __LIST__ format
                    content_for_agent = f'[name:{user_input}] Show main menu with services'
                else:
                    return {
                        "text": f"Welcome! Before we continue, please accept our privacy policy.\n\nDetails can be found here: https://npfpensions.com.ng/privacy-policy/",
                        "buttons": ["Accept Policy", "Decline Policy"],
                        "avatar_data": None
                    }

            number_to_service = {'1': 'audited accounts', '2': 'pencom', '3': 'fund management', '4': 'pension calculator', '5': 'whistle blowing', '6': 'faq', '7': 'customer login'}
            
            processed_content = user_input
            if user_input.strip() in number_to_service:
                processed_content = number_to_service[user_input.strip()]

            is_greeting = any(word in user_input.lower() for word in ['hi', 'hello', 'hey'])
            is_policy_acceptance = any(word in user_input.lower() for word in ['accept', 'yes', 'ok', 'okay', 'agree'])
            is_service_request = (user_input.strip().isdigit() and user_input.strip() in number_to_service) or any(keyword in processed_content.lower() for keyword in ['audited', 'pencom', 'fund', 'calculator', 'whistle', 'faq', 'login', 'services', 'registration', 'company'])
            
            has_accepted_policy = self.policy_accepted.get(thread_id, False)
            
            if is_policy_acceptance:
                self.policy_accepted[thread_id] = True
                logger.info(f"Policy accepted for user {thread_id}")
                # Let the LLM handle the service menu generation with __LIST__ format
                content_for_agent = f'[name:{user_input}] Policy accepted, show service menu'
            elif not has_accepted_policy and (is_greeting or is_service_request):
                logger.info(f"Initial contact (greeting or service request) from user {thread_id} before policy acceptance.")
                if thread_id not in self.assistant_identity:
                    _, assistant_name = self._get_static_image_base64()
                    self.assistant_identity[thread_id] = assistant_name
                else:
                    assistant_name = self.assistant_identity[thread_id]
                
                image_data = self._get_image_for_identity(assistant_name)
                user_name = ""
                if "[name:" in content:
                    try: user_name = content.split("[name:")[1].split("]")[0] + "! "
                    except: user_name = ""
                
                return {
                    "text": f"Hello, {user_name}I am {assistant_name}, your personal virtual assistant for NPF Pensions Ltd. I'm here to help you with information about our pension services, calculations, account access, and more.\n\nBefore we proceed, please review and accept our terms and conditions: https://npfpensions.com.ng/privacy-policy/",
                    "buttons": ["Accept Policy", "Decline Policy"],
                    "avatar_data": image_data
                }

            elif is_service_request and has_accepted_policy:
                logger.info(f"Service request with accepted policy: {user_input} -> {processed_content}")
                tool_result = get_pension_info(processed_content)
                
                if "No specific pre-written information found" not in tool_result:
                    text_response = tool_result.strip()
                    text_response += "\n\nType 0 to return to the main menu."
                    return {"text": text_response, "buttons": [], "avatar_data": None}
                else:
                    # If tool doesn't have info, let LLM handle it
                    content_for_agent = content
            elif not has_accepted_policy:
                 return {
                        "text": f"Welcome! Before we continue, please accept our privacy policy.\n\nDetails can be found here: https://npfpensions.com.ng/privacy-policy/",
                        "buttons": ["Accept Policy", "Decline Policy"],
                        "avatar_data": None
                    }
            else:
                # For all other cases, use the original content
                content_for_agent = content

            if not self.agent:
                logger.error("Agent not initialized")
                return {"text": "I'm currently unavailable. Please try again later.", "buttons": [], "avatar_data": None}

            # Use langgraph streaming pattern
            from langchain_core.messages import HumanMessage
            
            # Create the message object based on content_for_agent
            if isinstance(content_for_agent, str):
                message = HumanMessage(content=content_for_agent)
            elif isinstance(content_for_agent, list):
                message = HumanMessage(content=content_for_agent)
            else:
                message = HumanMessage(content=str(content_for_agent))

            config = {"configurable": {"thread_id": thread_id}, "recursion_limit": 100}
            response_content = ""

            # Stream the agent's response
            async for event in self.agent.astream_events({"messages": [message]}, config, version="v1"):
                if event["event"] == "on_chat_model_stream":
                    chunk = event["data"]["chunk"]
                    if chunk.content:
                        response_content += chunk.content
            
            # --- Parse __LIST__ or __BUTTONS__ DSL ---
            if "__LIST__" in response_content:
                try:
                    # No text part for lists, just the list payload
                    _, list_dsl = response_content.split("__LIST__", 1)
                    parts = [p.strip() for p in list_dsl.split("|")]
                    if len(parts) == 5:
                        options = [opt.strip() for opt in parts[4].split(",")]
                        logger.info(f"Agent parsed LIST: {parts}")
                        return {"list": {
                            "button_text": parts[0], "header": parts[1],
                            "body": parts[2], "section_title": parts[3],
                            "options": options
                        }, "avatar_data": None}
                except Exception as e:
                    logger.error(f"Failed to parse __LIST__ DSL: {e}")
                    return {"text": "Sorry, I had trouble formatting the question. Let's try another one.", "avatar_data": None}

            if "__BUTTONS__" in response_content:
                text_response, button_line = response_content.split("__BUTTONS__", 1)
                buttons = [b.strip() for b in button_line.split(",") if b.strip()]
                logger.info(f"Agent parsed BUTTONS: TEXT='{text_response.strip()}', BUTTONS={buttons}")
                return {"text": text_response.strip(), "buttons": buttons, "avatar_data": None}

            if not response_content:
                response_content = "I've processed that. How else can I assist you?"
            
            # Default response with menu option
            response_content += "\n\nType 0 to return to the main menu."

            logger.info(f"Agent final output: TEXT='{response_content}'")
            return {"text": response_content.strip(), "avatar_data": None}
                
        except Exception as e:
            logger.error(f"Error getting agent response: {e}", exc_info=True)
            return {"text": "I apologize, but I'm having trouble processing your request. Please try again.", "buttons": [], "avatar_data": None}

    def _extract_final_answer(self, raw_response: str) -> str:
        """Extract the response content, cleaning up any formatting."""
        try:
            if "Final Answer:" in raw_response:
                parts = raw_response.split("Final Answer:", 1)
                if len(parts) > 1:
                    return parts[1].strip()
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
        """Reset policy, identity, and memory for a user."""
        self.reset_policy_acceptance(thread_id)
        if thread_id in self.assistant_identity:
            del self.assistant_identity[thread_id]
            logger.info(f"Assistant identity reset for user {thread_id}")
        logger.info(f"Complete session reset for user {thread_id}")

    def _get_image_for_identity(self, identity: str) -> str:
        # NOTE: This returns a placeholder. You should replace this with your actual image loading logic.
        try:
            import base64, os
            image_paths = {
                "Toni": os.path.join(os.path.dirname(__file__), 'Gemini_Generated_Image_rkp2k2rkp2k2rkp2.png'),
                "Debby": os.path.join(os.path.dirname(__file__), 'Gemini_Generated_Image_rkp2k2rkp2k2rkp2.png')
            }
            image_path = image_paths.get(identity, image_paths["Toni"])
            if os.path.exists(image_path):
                with open(image_path, "rb") as image_file:
                    return base64.b64encode(image_file.read()).decode('utf-8')
            else:
                logger.warning(f"Image file not found for {identity}: {image_path}")
                return "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
        except Exception as e:
            logger.error(f"Error loading image for {identity}: {e}")
            return "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
        
    def _get_static_image_base64(self) -> tuple[str, str]:
        # NOTE: This returns a placeholder. You should replace this with your actual image loading logic.
        try:
            import base64, os, random
            image_data = [
                {"path": os.path.join(os.path.dirname(__file__), 'Gemini_Generated_Image_rkp2k2rkp2k2rkp2.png'), "name": "Debby"},
                {"path": os.path.join(os.path.dirname(__file__), 'Gemini_Generated_Image_rkp2k2rkp2k2rkp2.png'), "name": "Toni"}
            ]
            selected = random.choice(image_data)
            if os.path.exists(selected["path"]):
                with open(selected["path"], "rb") as image_file:
                    return base64.b64encode(image_file.read()).decode('utf-8'), selected["name"]
            else:
                return "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==", "Toni"
        except Exception as e:
            logger.error(f"Error loading random image: {e}")
            return "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==", "Toni"
