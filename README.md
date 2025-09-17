# NPF Pensions WhatsApp Agent

A WhatsApp bot for NPF Pensions Ltd that provides information about pension services using AI-powered conversations with voice support.

## Features

- **Text and Voice Message Support**: Handles both text messages and voice messages
- **AI-Powered Responses**: Uses Groq's LLM for intelligent responses
- **Interactive Buttons**: Supports WhatsApp interactive buttons for better UX
- **Speech-to-Text**: Converts voice messages to text using Groq's Whisper
- **Text-to-Speech**: Converts responses to audio using ElevenLabs
- **Memory Support**: Maintains conversation context using LangGraph

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Environment Variables

Create a `.env` file in the project root with the following variables:

```env
# WhatsApp API Configuration
WHATSAPP_TOKEN=your_whatsapp_token_here
WHATSAPP_PHONE_NUMBER_ID=your_phone_number_id_here
WHATSAPP_VERIFY_TOKEN=your_verify_token_here

# AI/LLM Configuration
GROQ_API_KEY=your_groq_api_key_here

# Text-to-Speech Configuration
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
ELEVENLABS_VOICE_ID=your_voice_id_here
TTS_MODEL_NAME=eleven_monolingual_v1

# Server Configuration
PORT=8000
```

### 3. Run the Application

```bash
python app.py
```

The server will start on `http://localhost:8000` (or the port specified in your .env file).

## API Endpoints

- `GET /` - Health check
- `GET /health` - Detailed health status
- `GET/POST /whatsapp` - WhatsApp webhook endpoint

## Services Offered

1. **Audited Accounts**
2. **PenCom**
3. **Fund Management**
4. **Pension Calculator**
5. **Whistle Blowing**
6. **FAQ**
7. **Customer Login**

## Architecture

- **FastAPI**: Web framework for handling HTTP requests
- **LangGraph**: Agent framework with memory support
- **Groq**: LLM provider for text generation and speech-to-text
- **ElevenLabs**: Text-to-speech conversion
- **WhatsApp Business API**: Message handling and sending
