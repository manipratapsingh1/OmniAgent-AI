"""Provider registry and model router factory."""
from __future__ import annotations

from typing import Dict, Optional

import structlog

from app.config import get_settings
from .provider import AIProvider
from .ollama_provider import OllamaProvider
from .model_router import ModelRouter

log = structlog.get_logger("provider_registry")
_settings = get_settings()


def build_providers() -> Dict[str, AIProvider]:
    """Build available providers based on configured API keys."""
    providers: Dict[str, AIProvider] = {}

    # Ollama is always available (local)
    try:
        providers["ollama"] = OllamaProvider()
    except Exception as e:
        log.warning("provider.ollama_unavailable", error=str(e))

    optional = [
        ("openai", "app.services.ai.openai_provider", "OpenAIProvider", "OPENAI_API_KEY"),
        ("anthropic", "app.services.ai.anthropic_provider", "AnthropicProvider", "ANTHROPIC_API_KEY"),
        ("gemini", "app.services.ai.gemini_provider", "GeminiProvider", "GEMINI_API_KEY"),
        ("groq", "app.services.ai.groq_provider", "GroqProvider", "GROQ_API_KEY"),
    ]

    for name, module_path, class_name, key_attr in optional:
        if not getattr(_settings, key_attr, ""):
            continue
        try:
            import importlib
            mod = importlib.import_module(module_path)
            cls = getattr(mod, class_name)
            providers[name] = cls()
            log.info("provider.registered", provider=name)
        except Exception as e:
            log.warning("provider.registration_failed", provider=name, error=str(e))

    return providers


_router: Optional[ModelRouter] = None


def get_model_router() -> ModelRouter:
    global _router
    if _router is None:
        _router = ModelRouter(build_providers())
    return _router
