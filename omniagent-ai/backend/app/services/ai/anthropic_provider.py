"""Anthropic Claude provider."""
from __future__ import annotations

from typing import AsyncIterator, Optional

import httpx
import structlog

from app.config import get_settings
from .provider import AIProvider

log = structlog.get_logger("anthropic_provider")
_settings = get_settings()


class AnthropicProvider(AIProvider):
    name = "anthropic"
    DEFAULT_MODEL = "claude-3-5-sonnet-20241022"

    def __init__(self):
        self.api_key = _settings.ANTHROPIC_API_KEY
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not configured")

    async def generate(self, prompt: str, **kwargs) -> str:
        model = kwargs.get("model") or self.DEFAULT_MODEL
        system = kwargs.get("system") or ""
        async with httpx.AsyncClient(timeout=120.0) as client:
            payload = {
                "model": model,
                "max_tokens": kwargs.get("max_tokens", 4096),
                "messages": [{"role": "user", "content": prompt}],
            }
            if system:
                payload["system"] = system
            r = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json=payload,
            )
            r.raise_for_status()
            data = r.json()
            blocks = data.get("content", [])
            return "".join(b.get("text", "") for b in blocks if b.get("type") == "text")

    async def stream(self, prompt: str, **kwargs) -> AsyncIterator[str]:
        model = kwargs.get("model") or self.DEFAULT_MODEL
        system = kwargs.get("system") or ""
        async with httpx.AsyncClient(timeout=120.0) as client:
            payload = {
                "model": model,
                "max_tokens": kwargs.get("max_tokens", 4096),
                "stream": True,
                "messages": [{"role": "user", "content": prompt}],
            }
            if system:
                payload["system"] = system
            async with client.stream(
                "POST",
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json=payload,
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
                        event = json.loads(chunk)
                        if event.get("type") == "content_block_delta":
                            text = event.get("delta", {}).get("text", "")
                            if text:
                                yield text
                    except Exception:
                        continue

    async def embed(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError("Anthropic does not provide embeddings; use Ollama or OpenAI")
