from .provider import AIProvider


class OpenAIProvider(AIProvider):
    name = "openai"

    async def generate(self, prompt: str, **kwargs) -> str:
        # Placeholder: integrate OpenAI SDK here
        return "(openai) " + prompt[:100]

    async def stream(self, prompt: str, **kwargs):
        # Simple streaming mock
        for i in range(0, len(prompt), 80):
            yield prompt[i:i+80]

    async def embed(self, texts: list[str]) -> list[list[float]]:
        # Return dummy embeddings
        return [[0.0] * 128 for _ in texts]
