from .provider import AIProvider
from app.llm.ollama_client import ollama
from app.config import get_settings


class OllamaProvider(AIProvider):
    name = "ollama"

    def __init__(self):
        self.settings = get_settings()
        self.client = ollama

    async def generate(self, prompt: str, **kwargs) -> str:
        """Generate a complete response from Ollama."""
        model = kwargs.get("model") or self.settings.OLLAMA_DEFAULT_MODEL
        system = kwargs.get("system")
        return await self.client.generate(prompt, model=model, system=system)

    async def stream(self, prompt: str, **kwargs):
        """Stream response chunks from Ollama."""
        model = kwargs.get("model") or self.settings.OLLAMA_DEFAULT_MODEL
        system = kwargs.get("system")
        async for chunk in self.client.stream(prompt, model=model, system=system):
            yield chunk

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings using Ollama embedding model."""
        return await self.client.embed(texts)

