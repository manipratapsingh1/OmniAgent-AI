from typing import Dict, Any


class VoiceHandler:
    """Server-side TTS/STT glue. Use external providers in production."""

    def __init__(self):
        pass

    def tts(self, text: str, voice: str = "default") -> Dict[str, Any]:
        # Return a simple payload; frontend can use Web Speech API instead
        return {"audio_url": None, "text": text}

    def transcribe(self, audio_bytes: bytes) -> str:
        # Placeholder: integrate with Whisper/other STT providers
        return "[transcribed speech]"
