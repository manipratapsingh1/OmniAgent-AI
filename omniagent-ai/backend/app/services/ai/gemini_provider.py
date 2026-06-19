"""Google Gemini provider."""
from __future__ import annotations

from typing import AsyncIterator

import httpx
import structlog

from app.config import get_settings
from .provider import AIProvider

log = structlog.get_logger("gemini_provider")
_settings = get_settings()


class GeminiProvider(AIProvider):
    name = "gemini"
    DEFAULT_MODEL = "gemini-2.0-flash"

    def __init__(self):
        self.api_key = _settings.GEMINI_API_KEY
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not configured")

    def _url(self, model: str, stream: bool = False) -> str:
        action = "streamGenerateContent" if stream else "generateContent"
        return (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{model}:{action}?key={self.api_key}"
        )

    def _payload(self, prompt: str, system: str | None) -> dict:
        parts = [{"text": prompt}]
        contents = [{"role": "user", "parts": parts}]
        payload: dict = {"contents": contents}
        if system:
            payload["systemInstruction"] = {"parts": [{"text": system}]}
        return payload

    async def generate(self, prompt: str, **kwargs) -> str:
        model = kwargs.get("model") or self.DEFAULT_MODEL
        async with httpx.AsyncClient(timeout=120.0) as client:
            r = await client.post(
                self._url(model),
                json=self._payload(prompt, kwargs.get("system")),
            )
            r.raise_for_status()
            data = r.json()
            candidates = data.get("candidates", [])
            if not candidates:
                return ""
            parts = candidates[0].get("content", {}).get("parts", [])
            return "".join(p.get("text", "") for p in parts)

    async def stream(self, prompt: str, **kwargs) -> AsyncIterator[str]:
        model = kwargs.get("model") or self.DEFAULT_MODEL
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream(
                "POST",
                self._url(model, stream=True),
                json=self._payload(prompt, kwargs.get("system")),
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line.strip():
                        continue
                    try:
                        import json
                        # Gemini streams JSON objects (may be array chunks)
                        line = line.lstrip("[,]")
                        if not line:
                            continue
                        data = json.loads(line)
                        candidates = data.get("candidates", [])
                        for c in candidates:
                            parts = c.get("content", {}).get("parts", [])
                            for p in parts:
                                text = p.get("text", "")
                                if text:
                                    yield text
                    except Exception:
                        continue

    async def embed(self, texts: list[str]) -> list[list[float]]:
        model = "text-embedding-004"
        results = []
        async with httpx.AsyncClient(timeout=60.0) as client:
            for text in texts:
                r = await client.post(
                    f"https://generativelanguage.googleapis.com/v1beta/models/"
                    f"{model}:embedContent?key={self.api_key}",
                    json={"content": {"parts": [{"text": text}]}},
                )
                r.raise_for_status()
                embedding = r.json().get("embedding", {}).get("values", [])
                results.append(embedding)
        return results
