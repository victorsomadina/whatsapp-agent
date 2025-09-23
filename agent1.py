# agent.py - Simplified for NPF Pensions, with button parsing.
import os
import logging
from typing import Any, Dict, List

from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq
from dotenv import load_dotenv

# Import the new prompt
from prompt1 import PENSION_AGENT_PROMPT

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _chat_llm() -> ChatOpenAI:
    """Return a streaming chat model."""
    return ChatGroq(
        api_key=os.getenv("GROQ_API_KEY"),
        model="meta-llama/llama-4-scout-17b-16e-instruct", # Using a capable model for instruction following
        temperature=0.1,
    )


class WhatsappAgent:
    """WhatsApp agent for NPF Pensions with memory and dynamic button support."""

    def __init__(self) -> None:
        self.memory = MemorySaver()
        self.llm = _chat_llm()
        self.agent = None

    async def initialize(self) -> None:
        """Initialize the agent without any external tools."""
        try:
            logger.info("Initializing NPF Pensions Agent (no tools)...")
            
            # The agent is created with an empty tool list
            self.agent = create_react_agent(
                model=self.llm,
                tools=[], # No tools are being used
                prompt=PENSION_AGENT_PROMPT,
                checkpointer=self.memory,
            )
            logger.info("NPF Pensions Agent ready with memory.")
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
        The response is parsed for a special '__BUTTONS__' directive
        to separate text from button labels.

        Returns:
            A dictionary like {"text": "Your response.", "buttons": ["Button 1", "Button 2"]}
        """
        if not self.agent:
            raise RuntimeError("Agent not initialized. Call initialize() first.")

        from langchain_core.messages import HumanMessage

        # Create the message object based on content type
        if isinstance(content, str):
            message = HumanMessage(content=content)
        elif isinstance(content, list):
            message = HumanMessage(content=content)
        else:
            message = HumanMessage(content=str(content))

        config = {"configurable": {"thread_id": thread_id}, "recursion_limit": 100}
        response_content = ""

        # Stream the agent's response
        async for event in self.agent.astream_events({"messages": [message]}, config, version="v1"):
            if event["event"] == "on_chat_model_stream":
                chunk = event["data"]["chunk"]
                if chunk.content:
                    response_content += chunk.content
        
        # Parse the response for text and buttons
        text, buttons = response_content, []
        if "__BUTTONS__" in response_content:
            text, button_line = response_content.split("__BUTTONS__", 1)
            text = text.strip()
            # Split buttons by comma and strip whitespace
            buttons = [b.strip() for b in button_line.split(",") if b.strip()]

        if not text:
            text = "I've processed that. How else can I assist you?"

        logger.info(f"Agent final output: TEXT='{text}', BUTTONS={buttons}")
        return {"text": text, "buttons": buttons}