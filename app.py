import base64
import httpx
from io import BytesIO
from typing import Dict, List
from fastapi import FastAPI, Request, Response, HTTPException, BackgroundTasks
import os
import logging
from dotenv import load_dotenv
import asyncio
from contextlib import asynccontextmanager
import tempfile
import json

# Import the new NPF Pensions agent
from agent import WhatsappAgent

from speech_to_text import SpeechToText
from text_to_speech import TextToSpeech

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

# WhatsApp API credentials
WHATSAPP_TOKEN = os.environ.get("WHATSAPP_TOKEN")
WHATSAPP_PHONE_NUMBER_ID = os.environ.get("WHATSAPP_PHONE_NUMBER_ID")
WHATSAPP_VERIFY_TOKEN = os.environ.get("WHATSAPP_VERIFY_TOKEN")

# Validate required environment variables
if not all([WHATSAPP_TOKEN, WHATSAPP_PHONE_NUMBER_ID, WHATSAPP_VERIFY_TOKEN]):
    logger.error("Missing one or more required WhatsApp environment variables.")
    exit(1)

# Global instances
pension_agent: WhatsappAgent | None = None
speech_to_text: SpeechToText | None = None
text_to_speech: TextToSpeech | None = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage the lifecycle of the FastAPI app and initialize components."""
    global pension_agent, speech_to_text, text_to_speech
    
    logger.info("Initializing NPF Pensions Agent and speech modules...")
    try:
        pension_agent = WhatsappAgent()
        await pension_agent.initialize()
        
        speech_to_text = SpeechToText()
        text_to_speech = TextToSpeech()
        
        logger.info("All components initialized successfully!")
    except Exception as e:
        logger.error(f"Failed to initialize components: {e}")
        # Nullify all on failure
        pension_agent = None
        speech_to_text = None
        text_to_speech = None

    yield

    logger.info("Cleaning up components...")
    if pension_agent:
        await pension_agent.cleanup()

# FastAPI app with lifespan management
app = FastAPI(
    title="NPF Pensions WhatsApp Agent",
    lifespan=lifespan
)

# --- WhatsApp API Communication ---

FB_BASE_URL = f"https://graph.facebook.com/v20.0/{WHATSAPP_PHONE_NUMBER_ID}/messages"
AUTH_HEADERS = {"Authorization": f"Bearer {WHATSAPP_TOKEN}"}

async def send_text_message(to: str, text: str):
    """Sends a simple text message with proper formatting."""
    # Clean up the text formatting for WhatsApp
    formatted_text = text.replace('\\n', '\n')  # Convert escaped newlines to actual newlines
    
    payload = {"messaging_product": "whatsapp", "to": to, "type": "text", "text": {"body": formatted_text}}
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(FB_BASE_URL, headers=AUTH_HEADERS, json=payload)
            response.raise_for_status()
            logger.info(f"Text message sent to {to}")
        except httpx.HTTPStatusError as e:
            logger.error(f"Error sending text message: {e.response.text}")

async def send_button_message(to: str, body: str, buttons: List[str]):
    """Sends an interactive message with up to 3 buttons."""
    # Validate button titles length (WhatsApp limit: 20 characters)
    validated_buttons = []
    for button in buttons[:3]:  # Max 3 buttons
        if len(button) > 20:
            # Truncate and add ellipsis if too long
            truncated = button[:17] + "..."
            validated_buttons.append(truncated)
            logger.warning(f"Button title truncated: '{button}' -> '{truncated}'")
        else:
            validated_buttons.append(button)
    
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {"text": body.replace('\\n', '\n')},  # Convert escaped newlines
            "action": {
                "buttons": [
                    {"type": "reply", "reply": {"id": f"btn_{i}", "title": btn}}
                    for i, btn in enumerate(validated_buttons)
                ]
            }
        }
    }
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(FB_BASE_URL, headers=AUTH_HEADERS, json=payload)
            response.raise_for_status()
            logger.info(f"Button message sent to {to} with {len(validated_buttons)} buttons")
        except httpx.HTTPStatusError as e:
            logger.error(f"Error sending button message: {e.response.text}")
            # Fallback to text message if button message fails
            await send_text_message(to, body)

async def send_audio_message(to: str, media_id: str):
    """Sends an audio message using the uploaded media ID."""
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "audio",
        "audio": {"id": media_id}
    }
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(FB_BASE_URL, headers=AUTH_HEADERS, json=payload)
            response.raise_for_status()
            logger.info(f"Audio message sent to {to}")
        except httpx.HTTPStatusError as e:
            logger.error(f"Error sending audio message: {e.response.text}")
            raise
            
async def download_media(media_id: str) -> bytes:
    """Download media from WhatsApp."""
    media_metadata_url = f"https://graph.facebook.com/v20.0/{media_id}"
    async with httpx.AsyncClient() as client:
        metadata_response = await client.get(media_metadata_url, headers=AUTH_HEADERS)
        metadata_response.raise_for_status()
        download_url = metadata_response.json().get("url")

        if not download_url:
            raise HTTPException(status_code=404, detail="Media URL not found.")

        media_response = await client.get(download_url, headers=AUTH_HEADERS)
        media_response.raise_for_status()
        return media_response.content

async def upload_media_to_whatsapp(media_content: bytes, mime_type: str) -> str | None:
    """Uploads media and returns the media ID."""
    upload_url = f"https://graph.facebook.com/v20.0/{WHATSAPP_PHONE_NUMBER_ID}/media"
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_file:
            temp_file.write(media_content)
            temp_file_path = temp_file.name

        with open(temp_file_path, "rb") as file_to_upload:
            form_data = {"messaging_product": "whatsapp", "type": mime_type}
            files = {"file": (os.path.basename(temp_file_path), file_to_upload, mime_type)}
            
            async with httpx.AsyncClient() as client:
                response = await client.post(upload_url, headers=AUTH_HEADERS, data=form_data, files=files)
                response.raise_for_status()
                result = response.json()
        
        return result.get("id")
    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)

# --- Webhook Handler ---

@app.api_route("/whatsapp", methods=["GET", "POST"])
async def whatsapp_handler(request: Request, background: BackgroundTasks) -> Response:
    """Lightweight handler to ACK Facebook immediately and delegate work to a background task."""
    if request.method == "GET":
        params = request.query_params
        if params.get("hub.verify_token") == WHATSAPP_VERIFY_TOKEN:
            return Response(content=params.get("hub.challenge"), status_code=200)
        return Response(content="Verification token mismatch", status_code=403)

    try:
        data = await request.json()
        changes = data["entry"][0]["changes"][0]["value"]
        messages = changes.get("messages", [])

        if not messages: # Ignore delivery receipts etc.
            return Response(status_code=200)
            
        message = messages[0]
        from_number = message["from"]
        
        #
        #
        # ✅ **THIS IS WHERE THE USER'S NAME IS EXTRACTED**
        user_name = changes.get("contacts", [{}])[0].get("profile", {}).get("name", "there")
        #
        #

        # Schedule the heavy processing in the background
        background.add_task(process_whatsapp_message, message, from_number, user_name)
        return Response(status_code=200) # ACK instantly
    except (KeyError, IndexError, json.JSONDecodeError):
        logger.warning("Malformed or unexpected webhook payload received")
        return Response(status_code=200) # Still ACK to prevent FB from resending

# --- Background Worker ---

async def process_whatsapp_message(message: dict, from_number: str, user_name: str):
    """Full processing pipeline for an incoming message."""
    try:
        message_type = message.get("type", "unknown")
        logger.info(f"[BG] Processing '{message_type}' from {from_number} ({user_name})")

        content_for_agent = ""
        should_respond_with_audio = False

        # ✅ **THE NAME IS PREPENDED TO THE MESSAGE FOR THE AGENT HERE**
        if message_type == "text":
            content_for_agent = f'[name:{user_name}] {message["text"]["body"]}'
        
        elif message_type == "interactive" and message["interactive"]["type"] == "button_reply":
            button_title = message["interactive"]["button_reply"]["title"]
            content_for_agent = f'[name:{user_name}] [User clicked button]: "{button_title}"'

        elif message_type == "audio":
            if not speech_to_text:
                await send_text_message(from_number, "Sorry, the speech service is currently unavailable.")
                return
            try:
                audio_bytes = await download_media(message["audio"]["id"])
                transcribed_text = await speech_to_text.transcribe(audio_bytes)
                content_for_agent = f'[name:{user_name}] [Voice message transcribed]: {transcribed_text}'
                should_respond_with_audio = True
            except Exception as e:
                logger.error(f"[BG] STT failed: {e}")
                await send_text_message(from_number, "Sorry, I couldn't process your voice message. Please try again.")
                return
        
        else:
            await send_text_message(from_number, "I can only process text, voice messages, and button clicks.")
            return

        # --- Call Agent ---
        if not pension_agent:
            await send_text_message(from_number, "I'm currently unavailable. Please try again later.")
            return

        thread_id = from_number.replace("+", "")
        agent_response = await pension_agent.get_response(content_for_agent, thread_id)
        
        response_text = agent_response["text"]
        buttons = agent_response.get("buttons", [])

        # --- Send Reply ---
        if should_respond_with_audio and text_to_speech:
            try:
                audio_bytes = await text_to_speech.synthesize(response_text)
                media_id = await upload_media_to_whatsapp(audio_bytes, "audio/mpeg")
                if media_id:
                    await send_audio_message(from_number, media_id)
                else: 
                    await send_text_message(from_number, response_text)
            except Exception as e:
                logger.error(f"[BG] TTS or audio upload failed: {e}")
                await send_text_message(from_number, response_text)
        
        elif buttons:
            await send_button_message(from_number, response_text, buttons)
        else:
            await send_text_message(from_number, response_text)

    except Exception as e:
        logger.exception("[BG] Unhandled exception in background task")
        try:
            await send_text_message(from_number, "Something went wrong. Please try again later.")
        except Exception:
            pass # Avoid error loops

# --- Health Check and Root Endpoints ---

@app.get("/")
async def root():
    return {"message": "NPF Pensions WhatsApp Agent is running!"}

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "agent_status": "initialized" if pension_agent else "not_initialized",
        "speech_to_text_status": "initialized" if speech_to_text else "not_initialized",
        "text_to_speech_status": "initialized" if text_to_speech else "not_initialized",
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)