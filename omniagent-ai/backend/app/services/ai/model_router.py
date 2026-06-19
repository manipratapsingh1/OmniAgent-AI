"""
Intelligent multi-model router with automatic failover.

Routing rules:
  - coding tasks  → Anthropic / OpenAI
  - research      → Gemini
  - fast queries  → Groq
  - offline/dev   → Ollama
"""
from __future__ import annotations

import re
from enum import Enum
from typing import AsyncIterator, Optional

import structlog

from app.config import get_settings
from .provider import AIProvider
from .ollama_provider import OllamaProvider

log = structlog.get_logger("model_router")
_settings = get_settings()


class TaskType(str, Enum):
    CODING = "coding"
    RESEARCH = "research"
    FAST = "fast"
    GENERAL = "general"


_CODING_PATTERNS = [
    r"\b(code|debug|refactor|implement|function|class|api|sql|python|javascript|typescript|react|bug)\b",
    r"\b(write\s+a\s+(script|program|function|class))\b",
]
_RESEARCH_PATTERNS = [
    r"\b(research|analyze|compare|investigate|study|report|summarize|deep\s+dive)\b",
    r"\b(what\s+are\s+the\s+(latest|recent|current))\b",
]
_FAST_PATTERNS = [
    r"\b(quick|brief|short|simple|fast|one\s+line|tl;dr)\b",
]


def classify_task(query: str, explicit: Optional[str] = None) -> TaskType:
    if explicit:
        try:
            return TaskType(explicit)
        except ValueError:
            pass
    lower = query.lower()
    for p in _CODING_PATTERNS:
        if re.search(p, lower):
            return TaskType.CODING
    for p in _RESEARCH_PATTERNS:
        if re.search(p, lower):
            return TaskType.RESEARCH
    for p in _FAST_PATTERNS:
        if re.search(p, lower):
            return TaskType.FAST
    return TaskType.GENERAL


class ModelRouter:
    """Route queries to the best available provider with automatic fallback."""

    PROVIDER_PRIORITY = {
        TaskType.CODING: ["anthropic", "openai", "ollama"],
        TaskType.RESEARCH: ["gemini", "openai", "ollama"],
        TaskType.FAST: ["groq", "ollama"],
        TaskType.GENERAL: ["ollama", "openai", "groq"],
    }

    def __init__(self, providers: dict[str, AIProvider]):
        self.providers = providers
        self._fallback = OllamaProvider()

    def select_provider(
        self,
        query: str,
        task_type: Optional[str] = None,
        preferred: Optional[str] = None,
    ) -> tuple[AIProvider, str]:
        if preferred and preferred in self.providers:
            return self.providers[preferred], preferred

        task = classify_task(query, task_type)
        priority = self.PROVIDER_PRIORITY.get(task, ["ollama"])

        # Apply config overrides
        config_map = {
            TaskType.CODING: _settings.CODING_PROVIDER,
            TaskType.RESEARCH: _settings.RESEARCH_PROVIDER,
            TaskType.FAST: _settings.FAST_PROVIDER,
        }
        override = config_map.get(task)
        if override and override in self.providers:
            return self.providers[override], override

        for name in priority:
            if name in self.providers:
                log.info("model_router.selected", task=task.value, provider=name)
                return self.providers[name], name

        return self._fallback, "ollama"

    def _fallback_chain(self, primary: str) -> list[str]:
        chain = [primary, _settings.FALLBACK_PROVIDER]
        for name in self.providers:
            if name not in chain:
                chain.append(name)
        seen: set[str] = set()
        result = []
        for p in chain:
            if p not in seen:
                seen.add(p)
                result.append(p)
        return result

    async def generate(
        self,
        prompt: str,
        query: str = "",
        provider: Optional[str] = None,
        task_type: Optional[str] = None,
        **kwargs,
    ) -> tuple[str, str]:
        """Generate with automatic failover. Returns (response, provider_used)."""
        _, primary_name = self.select_provider(query or prompt, task_type, provider)
        chain = self._fallback_chain(primary_name)

        last_error = None
        for name in chain:
            if name not in self.providers:
                continue
            p = self.providers[name]
            try:
                result = await p.generate(prompt, **kwargs)
                if name != primary_name:
                    log.warning("model_router.failover", primary=primary_name, used=name)
                return result, name
            except Exception as e:
                last_error = e
                log.warning("model_router.provider_failed", provider=name, error=str(e))

        raise RuntimeError(f"All providers failed. Last error: {last_error}")

    async def stream(
        self,
        prompt: str,
        query: str = "",
        provider: Optional[str] = None,
        task_type: Optional[str] = None,
        **kwargs,
    ) -> AsyncIterator[str]:
        """Stream with automatic failover on first-chunk failure."""
        _, primary_name = self.select_provider(query or prompt, task_type, provider)
        chain = self._fallback_chain(primary_name)

        for name in chain:
            if name not in self.providers:
                continue
            p = self.providers[name]
            try:
                got_token = False
                async for token in p.stream(prompt, **kwargs):
                    got_token = True
                    yield token
                if got_token:
                    return
            except Exception as e:
                log.warning("model_router.stream_failed", provider=name, error=str(e))
                continue

        yield "Error: All LLM providers are unavailable. Please try again later."
