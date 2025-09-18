import os
from typing import Optional
import requests
from elevenlabs import ElevenLabs, Voice, VoiceSettings
from dotenv import load_dotenv

load_dotenv()

class TextToSpeechError(Exception):
    """Custom exception for text-to-speech errors."""
    pass

class TextToSpeech:
    """A class to handle text-to-speech conversion using ElevenLabs."""

    # Required environment variables
    REQUIRED_ENV_VARS = ["ELEVENLABS_API_KEY", "ELEVENLABS_VOICE_ID"]

    def __init__(self):
        """Initialize the TextToSpeech class and validate environment variables."""
        self._validate_env_vars()
        self._client: Optional[ElevenLabs] = None

    @property
    def client(self) -> ElevenLabs:
        """Get or create ElevenLabs client instance using singleton pattern."""
        if self._client is None:
            self._client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))
        return self._client

    def _validate_env_vars(self) -> None:
        """Validate that all required environment variables are set."""
        missing_vars = [var for var in self.REQUIRED_ENV_VARS if not os.getenv(var)]
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

    async def synthesize(self, text: str) -> bytes:
        """Convert text to speech using ElevenLabs.

        Args:
            text: Text to convert to speech

        Returns:
            bytes: Audio data

        Raises:
            ValueError: If the input text is empty or too long
            TextToSpeechError: If the text-to-speech conversion fails
        """
        if not text.strip():
            raise ValueError("Input text cannot be empty")

        if len(text) > 5000:  
            raise ValueError("Input text exceeds maximum length of 5000 characters")

        try:
            # Use the new ElevenLabs API
            voice_id = os.getenv("ELEVENLABS_VOICE_ID")
            model = os.getenv("TTS_MODEL_NAME", "eleven_monolingual_v1")
            
            # Create voice settings
            voice_settings = VoiceSettings(
                stability=0.5, 
                similarity_boost=0.5,
                style=0.0,
                use_speaker_boost=True
            )
            
            # Generate audio using the new API
            audio_bytes = self.client.text_to_speech.convert(
                text=text,
                voice_id=voice_id,
                model_id=model,
                voice_settings=voice_settings
            )
            
            if not audio_bytes:
                raise TextToSpeechError("Generated audio is empty")

            return audio_bytes

        except Exception as e:
            # Fallback to direct API call
            try:
                url = f"https://api.elevenlabs.io/v1/text-to-speech/{os.getenv('ELEVENLABS_VOICE_ID')}"
                headers = {
                    "Accept": "audio/mpeg",
                    "Content-Type": "application/json",
                    "xi-api-key": os.getenv("ELEVENLABS_API_KEY")
                }
                data = {
                    "text": text,
                    "model_id": os.getenv("TTS_MODEL_NAME", "eleven_monolingual_v1"),
                    "voice_settings": {
                        "stability": 0.5,
                        "similarity_boost": 0.5,
                        "style": 0.0,
                        "use_speaker_boost": True
                    }
                }
                
                response = requests.post(url, json=data, headers=headers)
                response.raise_for_status()
                
                if not response.content:
                    raise TextToSpeechError("Generated audio is empty")
                    
                return response.content
                
            except Exception as fallback_error:
                raise TextToSpeechError(f"Text-to-speech conversion failed: {str(e)}. Fallback also failed: {str(fallback_error)}") from e