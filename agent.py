import os
import json
import logging
from typing import Any, Dict, List
from langchain.agents import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq
from langchain_core.tools import tool
from dotenv import load_dotenv
from prompt import PENSION_AGENT_PROMPT


load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _chat_llm() -> ChatOpenAI:
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

    async def initialize(self) -> None:
        """Initialize the ReAct agent with tools."""
        try:
            logger.info("Initializing NPF Pensions ReAct Agent...")
            
            # Create a prompt template for the ReAct agent
            from langchain_core.prompts import PromptTemplate
            prompt_template = PromptTemplate(
                input_variables=["input", "agent_scratchpad", "tools", "tool_names"],
                template=PENSION_AGENT_PROMPT
            )
            
            # Create tools for the agent
            tools = self._create_tools()
            
            # Create the ReAct agent
            self.agent = create_react_agent(
                llm=self.llm,
                tools=tools,
                prompt=prompt_template
            )
            
            logger.info("NPF Pensions ReAct Agent ready with memory and tools.")
        except Exception as e:
            logger.error(f"Agent initialization failed: {e}", exc_info=True)
            raise

    def _create_tools(self) -> List:
        """Create tools for the ReAct agent."""
        @tool
        def get_pension_calculation_info() -> str:
            """Get information about pension calculation requirements and process."""
            return """
            To calculate your pension, I need the following information:
            1. Your current age
            2. Your expected retirement age
            3. Your monthly contributions to the pension scheme
            4. The number of years you've been contributing
            5. Your current account balance (if known)
            
            Once I have this information, I can provide you with a personalized pension calculation.
            """
        
        @tool
        def get_services_info() -> str:
            """Get information about NPF Pensions Ltd services."""
            return """
            NPF Pensions Ltd offers the following services:
            1. Retirement Savings Account (RSA) management
            2. Pension contribution processing
            3. Retirement benefits calculation
            4. Pension fund investment options
            5. Pension transfer and rollover
            6. Pension withdrawal and payment
            7. General pension advice and guidance
            """
        
        @tool
        def get_registration_info() -> str:
            """Get information about how to register with NPF Pensions Ltd."""
            return """
            To register with NPF Pensions Ltd:
            1. Visit our website at npfpensions.com
            2. Click on the "Register" button
            3. Fill out the registration form with your personal details
            4. Choose a username and password
            5. Verify your email address
            6. Upload required documents (ID, utility bill)
            7. Wait for account verification
            
            You can also visit any of our branches nationwide for in-person registration.
            """
        
        @tool
        def get_company_info() -> str:
            """Get information about NPF Pensions Ltd company background."""
            return """
            NPF Pensions Ltd is a leading Pension Fund Administrator (PFA) in Nigeria, 
            licensed by the National Pension Commission (PenCom). We were incorporated 
            on 21st October 2013 to cater to the unique needs of the Nigeria Police Force 
            under the Contributory Pension Scheme (CPS). Our goal is to effectively manage 
            police personnel pensions, Group Life Assurance, and Health Insurance Schemes.
            """
        
        return [get_pension_calculation_info, get_services_info, get_registration_info, get_company_info]

    async def cleanup(self) -> None:
        """Cleanup resources."""
        logger.info("Cleaning up WhatsappAgent...")
        self.agent = None

    async def get_response(self, content: Any, thread_id: str) -> Dict[str, Any]:
        """
        Get a response from the ReAct agent with AI-generated images.
        
        Returns:
            A dictionary like {"text": "Your response.", "buttons": ["Button 1", "Button 2"], "avatar_data": "base64_image_data"}
        """
        try:
            from langchain_core.messages import HumanMessage, SystemMessage
            messages = [
                SystemMessage(content=PENSION_AGENT_PROMPT),
                HumanMessage(content=content)
            ]
            response = await self.llm.ainvoke(messages)
            raw_response = response.content
            
            # Extract only the Final Answer from ReAct format
            text_response = self._extract_final_answer(raw_response)
            
            # Include static base64 image with every response
            image_data = self._get_static_image_base64()
            
            # Parse buttons from the response
            buttons = []
            if "__BUTTONS__" in text_response:
                text_response, button_line = text_response.split("__BUTTONS__", 1)
                text_response = text_response.strip()
                # Split buttons by comma and strip whitespace
                buttons = [b.strip() for b in button_line.split(",") if b.strip()]

            if not text_response:
                text_response = "I've processed that. How else can I assist you?"
            
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
        """Extract only the Final Answer from ReAct format response."""
        try:
            # Look for "Final Answer:" in the response
            if "Final Answer:" in raw_response:
                # Split by "Final Answer:" and take everything after it
                parts = raw_response.split("Final Answer:", 1)
                if len(parts) > 1:
                    final_answer = parts[1].strip()
                    lines = final_answer.split('\n')
                    clean_lines = []
                    for line in lines:
                        if not line.strip().startswith(('Thought:', 'Action:', 'Observation:', 'Action Input:')):
                            clean_lines.append(line)
                        else:
                            break  # Stop at the first non-Final Answer line
                    return '\n'.join(clean_lines).strip()
            
            # If no "Final Answer:" found, try to clean up the response by removing ReAct patterns
            lines = raw_response.split('\n')
            clean_lines = []
            skip_until_final = False
            
            for line in lines:
                line_stripped = line.strip()
                
                # Skip ReAct reasoning lines
                if line_stripped.startswith(('Thought:', 'Action:', 'Observation:', 'Action Input:')):
                    skip_until_final = True
                    continue
                
                # If we hit a line that doesn't start with ReAct keywords, start collecting
                if skip_until_final and not line_stripped.startswith(('Thought:', 'Action:', 'Observation:', 'Action Input:')):
                    skip_until_final = False
                
                if not skip_until_final:
                    clean_lines.append(line)
            
            result = '\n'.join(clean_lines).strip()
            return result if result else raw_response
            
        except Exception as e:
            logger.warning(f"Error extracting final answer: {e}")
            return raw_response
    
    def _get_static_image_base64(self) -> str:
        """Return a randomly selected base64 encoded image for every response."""
        try:
            import base64
            import os
            import random
            
            # List of available ChatGPT generated images
            image_paths = [                
                r"C:\Users\hp\Downloads\NPFPension\whatsapp-agent\ChatGPT Image Sep 18, 2025, 05_25_41 PM.png",
                r"C:\Users\hp\Downloads\NPFPension\whatsapp-agent\ChatGPT Image Sep 18, 2025, 05_25_19 PM.png",
            ]
            
            # Randomly select an image
            selected_path = random.choice(image_paths)
            
            if os.path.exists(selected_path):
                with open(selected_path, "rb") as image_file:
                    image_data = image_file.read()
                    base64_image = base64.b64encode(image_data).decode('utf-8')
                    logger.info(f"Loaded random image from {os.path.basename(selected_path)}, size: {len(image_data)} bytes")
                    return base64_image
            else:
                logger.warning(f"Selected image file not found: {selected_path}")
                # Try fallback to any available image
                for fallback_path in image_paths:
                    if os.path.exists(fallback_path):
                        with open(fallback_path, "rb") as image_file:
                            image_data = image_file.read()
                            base64_image = base64.b64encode(image_data).decode('utf-8')
                            logger.info(f"Using fallback image from {os.path.basename(fallback_path)}, size: {len(image_data)} bytes")
                            return base64_image
                
                # Final fallback to placeholder
                return "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
                
        except Exception as e:
            logger.error(f"Error loading random image: {e}")
            # Fallback to placeholder
            return "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="