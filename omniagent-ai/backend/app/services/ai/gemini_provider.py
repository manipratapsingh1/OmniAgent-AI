from .provider import AIProvider


class GeminiProvider(AIProvider):
    name = "gemini"

    async def generate(self, prompt: str, **kwargs) -> str:
        # Placeholder for Gemini integration
        return "(gemini) " + prompt[:100]

    async def stream(self, prompt: str, **kwargs):
        for i in range(0, len(prompt), 80):
            yield prompt[i:i+80]

    async def embed(self, texts: list[str]) -> list[list[float]]:
        return [[0.0] * 128 for _ in texts]
