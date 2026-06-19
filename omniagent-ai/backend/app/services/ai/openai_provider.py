"""OpenAI provider with real SDK integration."""
from __future__ import annotations

from typing import AsyncIterator

import structlog

from app.config import get_settings
from .provider import AIProvider

log = structlog.get_logger("openai_provider")
_settings = get_settings()


class OpenAIProvider(AIProvider):
    name = "openai"
    DEFAULT_MODEL = "gpt-4o-mini"

    def __init__(self):
        self.api_key = _settings.OPENAI_API_KEY
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not configured")
        try:
            from openai import AsyncOpenAI
            self.client = AsyncOpenAI(api_key=self.api_key)
        except ImportError as e:
            raise RuntimeError("openai package not installed") from e

    def _messages(self, prompt: str, system: str | None) -> list:
        msgs = []
        if system:
            msgs.append({"role": "system", "content": system})
        msgs.append({"role": "user", "content": prompt})
        return msgs

    async def generate(self, prompt: str, **kwargs) -> str:
        model = kwargs.get("model") or self.DEFAULT_MODEL
        response = await self.client.chat.completions.create(
            model=model,
            messages=self._messages(prompt, kwargs.get("system")),
            temperature=kwargs.get("temperature", 0.7),
        )
        return response.choices[0].message.content or ""

    async def stream(self, prompt: str, **kwargs) -> AsyncIterator[str]:
        model = kwargs.get("model") or self.DEFAULT_MODEL
        stream = await self.client.chat.completions.create(
            model=model,
            messages=self._messages(prompt, kwargs.get("system")),
            temperature=kwargs.get("temperature", 0.7),
            stream=True,
        )
        async for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta

    async def embed(self, texts: list[str]) -> list[list[float]]:
        response = await self.client.embeddings.create(
            model="text-embedding-3-small", input=texts
        )
        return [item.embedding for item in response.data]
