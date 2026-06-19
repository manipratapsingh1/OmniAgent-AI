"""Groq provider — OpenAI-compatible fast inference API."""
from __future__ import annotations

from typing import AsyncIterator

import httpx
import structlog

from app.config import get_settings
from .provider import AIProvider

log = structlog.get_logger("groq_provider")
_settings = get_settings()


class GroqProvider(AIProvider):
    name = "groq"
    DEFAULT_MODEL = "llama-3.3-70b-versatile"
    BASE_URL = "https://api.groq.com/openai/v1"

    def __init__(self):
        self.api_key = _settings.GROQ_API_KEY
        if not self.api_key:
            raise ValueError("GROQ_API_KEY not configured")

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

    def _messages(self, prompt: str, system: str | None) -> list:
        msgs = []
        if system:
            msgs.append({"role": "system", "content": system})
        msgs.append({"role": "user", "content": prompt})
        return msgs

    async def generate(self, prompt: str, **kwargs) -> str:
        model = kwargs.get("model") or self.DEFAULT_MODEL
        async with httpx.AsyncClient(timeout=60.0) as client:
            r = await client.post(
                f"{self.BASE_URL}/chat/completions",
                headers=self._headers(),
                json={
                    "model": model,
                    "messages": self._messages(prompt, kwargs.get("system")),
                    "temperature": kwargs.get("temperature", 0.7),
                },
            )
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"] or ""

    async def stream(self, prompt: str, **kwargs) -> AsyncIterator[str]:
        model = kwargs.get("model") or self.DEFAULT_MODEL
        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream(
                "POST",
                f"{self.BASE_URL}/chat/completions",
                headers=self._headers(),
                json={
                    "model": model,
                    "messages": self._messages(prompt, kwargs.get("system")),
                    "stream": True,
                    "temperature": kwargs.get("temperature", 0.7),
                },
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    chunk = line[6:]
                    if chunk == "[DONE]":
                        break
                    try:
                        import json
                        data = json.loads(chunk)
                        delta = data["choices"][0].get("delta", {}).get("content", "")
                        if delta:
                            yield delta
                    except Exception:
                        continue

    async def embed(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError("Groq does not provide embeddings; use Ollama or OpenAI")
