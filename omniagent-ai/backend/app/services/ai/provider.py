from typing import Any, AsyncIterator, Dict, Optional


class AIProvider:
    """Base AI provider interface."""

    name: str = "base"

    async def generate(self, prompt: str, **kwargs) -> str:
        raise NotImplementedError()

    async def stream(self, prompt: str, **kwargs) -> AsyncIterator[str]:
        raise NotImplementedError()

    async def embed(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError()
"""
LLM Provider Abstraction

Supports multiple LLM providers (OpenAI, Ollama, etc.) with unified interface.
Enables easy switching between providers and future extensibility.
"""

from typing import AsyncIterator, Optional, List
from abc import ABC, abstractmethod
import structlog

log = structlog.get_logger("llm_provider")


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    @abstractmethod
    async def generate(self, prompt: str, system: Optional[str] = None, model: Optional[str] = None) -> str:
        """Generate a non-streaming response."""
        pass
    
    @abstractmethod
    async def stream(self, prompt: str, system: Optional[str] = None, model: Optional[str] = None) -> AsyncIterator[str]:
        """Generate a streaming response."""
        pass


class OllamaProvider(LLMProvider):
    """Ollama LLM Provider."""
    
    def __init__(self):
        from app.llm.ollama_client import ollama
        self.client = ollama
    
    async def generate(self, prompt: str, system: Optional[str] = None, model: Optional[str] = None) -> str:
        """Generate response using Ollama."""
        return await self.client.generate(prompt=prompt, system=system, model=model)
    
    async def stream(self, prompt: str, system: Optional[str] = None, model: Optional[str] = None) -> AsyncIterator[str]:
        """Stream response using Ollama."""
        async for token in self.client.stream(prompt=prompt, system=system, model=model):
            yield token


class OpenAIProvider(LLMProvider):
    """OpenAI LLM Provider (future implementation)."""
    
    def __init__(self, api_key: Optional[str] = None):
        import os
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key not configured")
        
        try:
            from openai import AsyncOpenAI
            self.client = AsyncOpenAI(api_key=self.api_key)
        except ImportError:
            raise RuntimeError("OpenAI client not installed. Install with: pip install openai")
    
    async def generate(self, prompt: str, system: Optional[str] = None, model: Optional[str] = None) -> str:
        """Generate response using OpenAI."""
        model = model or "gpt-4"
        messages = []
        
        if system:
            messages.append({"role": "system", "content": system})
        
        messages.append({"role": "user", "content": prompt})
        
        response = await self.client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.7,
        )
        
        return response.choices[0].message.content or ""
    
    async def stream(self, prompt: str, system: Optional[str] = None, model: Optional[str] = None) -> AsyncIterator[str]:
        """Stream response using OpenAI."""
        model = model or "gpt-4"
        messages = []
        
        if system:
            messages.append({"role": "system", "content": system})
        
        messages.append({"role": "user", "content": prompt})
        
        stream = await self.client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.7,
            stream=True,
        )
        
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content


def get_provider(provider: str = "ollama", api_key: Optional[str] = None) -> LLMProvider:
    """
    Get an LLM provider instance.
    
    Args:
        provider: Provider name ("ollama" or "openai")
        api_key: API key for the provider (if needed)
    
    Returns:
        LLMProvider instance
    """
    provider = provider.lower()
    
    if provider == "ollama":
        log.info("provider.initialized", provider="ollama")
        return OllamaProvider()
    
    elif provider == "openai":
        log.info("provider.initialized", provider="openai")
        return OpenAIProvider(api_key=api_key)
    
    else:
        raise ValueError(f"Unknown provider: {provider}. Supported: ollama, openai")
