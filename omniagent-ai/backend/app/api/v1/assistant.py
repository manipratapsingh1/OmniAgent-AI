from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from typing import Dict, Any, AsyncGenerator
from app.deps import db_session, current_user
from app.services.ai.service import AIService
from app.services.ai.voice_handler import VoiceHandler
import json

router = APIRouter()
_ai = AIService()
_voice = VoiceHandler()


async def _stream_response(prompt: str, provider: str | None = None, stream: bool = False) -> AsyncGenerator[str, None]:
    """Stream response chunks as Server-Sent Events."""
    if stream:
        # Immediate first-stage placeholder to reduce perceived latency
        meta = json.dumps({"type": "status", "data": {"message": "Searching documents..."}})
        yield f"data: {meta}\n\n"

        async for chunk in _ai.stream(prompt, provider=provider):
            data = json.dumps({"type": "chunk", "data": {"text": chunk}})
            yield f"data: {data}\n\n"
    else:
        resp = await _ai.generate(prompt, provider=provider)
        data = json.dumps({"type": "complete", "data": {"text": resp}})
        yield f"data: {data}\n\n"


@router.post("/chat")
async def chat(
    message: Dict[str, Any],
    db=Depends(db_session),
    user=Depends(current_user)
):
    """Chat endpoint supporting both streaming and non-streaming modes.
    
    Query params:
    - stream: bool (default: false) - enable Server-Sent Events streaming
    
    Request body:
    - message: str - the user message
    - prompt: str (alias for message)
    - provider: str (optional provider name such as ollama, openai, gemini)
    """
    try:
        prompt = message.get("message") or message.get("prompt")
        if not prompt:
            raise HTTPException(status_code=400, detail="message is required")

        provider = message.get("provider")
        stream = message.get("stream", False)

        if stream:
            return StreamingResponse(
                _stream_response(prompt, provider=provider, stream=True),
                media_type="text/event-stream"
            )
        else:
            resp = await _ai.generate(prompt, provider=provider)
            return {"ok": True, "response": resp}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/transcribe")
async def transcribe(file: UploadFile = File(...)):
    """Transcribe audio file to text using configured TTS provider."""
    data = await file.read()
    text = _voice.transcribe(data)
    return {"text": text}


@router.post("/tts")
async def tts(payload: Dict[str, Any]):
    """Convert text to speech using configured TTS provider."""
    text = payload.get("text", "")
    return _voice.tts(text)

