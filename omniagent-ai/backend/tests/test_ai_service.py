"""Unit tests for AIService provider selection."""

from app.services.ai.service import AIService


def test_choose_provider_by_name():
    service = AIService()
    assert service.choose_provider("ollama").name == "ollama"
    assert service.choose_provider("openai").name == "openai"
    assert service.choose_provider("gemini").name == "gemini"


def test_choose_provider_defaults_to_ollama():
    service = AIService()
    provider = service.choose_provider()
    assert provider.name == "ollama"


def test_choose_provider_ignores_model_name_lookup():
    """Regression: model names like llama3.2 must not be used as provider keys."""
    service = AIService()
    provider = service.choose_provider("llama3.2")
    assert provider.name == "ollama"
