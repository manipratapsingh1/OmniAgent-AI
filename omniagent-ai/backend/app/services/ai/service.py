from typing import Optional, Any
from app.config import get_settings
from .provider import AIProvider
from .openai_provider import OpenAIProvider
from .ollama_provider import OllamaProvider
from .gemini_provider import GeminiProvider
from .knowledge_search import KnowledgeSearchService
from app.cache import key_for_text, get_json, set_json


_settings = get_settings()


class AIService:
    def __init__(self, db: Optional[Any] = None, provider: Optional[str] = None):
        self.settings = get_settings()
        self.db = db
        self.default_provider = provider or "ollama"
        # Register providers
        self.providers: dict[str, AIProvider] = {
            OpenAIProvider.name: OpenAIProvider(),
            OllamaProvider.name: OllamaProvider(),
            GeminiProvider.name: GeminiProvider(),
        }

    def choose_provider(self, provider_name: Optional[str] = None) -> AIProvider:
        name = provider_name or self.default_provider or "ollama"
        if name in self.providers:
            return self.providers[name]
        return self.providers["ollama"]

    async def generate(self, prompt: str, provider: Optional[str] = None, **kwargs) -> str:
        p = self.choose_provider(provider)
        # Prompt/response caching to reduce repeated model calls for identical prompts
        try:
            model = kwargs.get("model") or getattr(_settings, "FAST_RAG_MODEL", "phi3:mini")
            cache_key = key_for_text("prompt", model, prompt)
            cached = get_json(cache_key)
            if cached:
                return cached
        except Exception:
            cached = None

        resp = await p.generate(prompt, **kwargs)

        try:
            ttl = getattr(_settings, "CACHE_TTL_SECONDS", 300)
            set_json(cache_key, resp, ex=ttl)
        except Exception:
            pass

        return resp

    async def stream(self, prompt: str, provider: Optional[str] = None, **kwargs):
        p = self.choose_provider(provider)
        async for chunk in p.stream(prompt, **kwargs):
            yield chunk

    async def embed(self, texts: list[str], provider: Optional[str] = None):
        p = self.choose_provider(provider)
        return await p.embed(texts)

    async def query(
        self,
        question: str,
        model: Optional[str] = None,
        provider: Optional[str] = None,
        search_knowledge_base: bool = False,
        k: int = 5,
        system_prompt: Optional[str] = None,
    ) -> dict:
        provider_instance = self.choose_provider(provider)
        knowledge_sources = []
        if search_knowledge_base:
            if self.db is None:
                raise ValueError("Database session is required for knowledge base search.")
            knowledge_search = KnowledgeSearchService(self.db)
            knowledge_sources = await knowledge_search.search_knowledge_base(question, k=k)

        prompt = self._build_prompt(question, knowledge_sources, system_prompt)
        answer = await provider_instance.generate(
            prompt=prompt,
            model=model,
            system=system_prompt,
        )

        return {
            "answer": answer,
            "sources": knowledge_sources,
            "used_knowledge_base": bool(knowledge_sources),
        }

    async def stream_query(
        self,
        question: str,
        model: Optional[str] = None,
        provider: Optional[str] = None,
        search_knowledge_base: bool = False,
        k: int = 5,
        system_prompt: Optional[str] = None,
    ):
        provider_instance = self.choose_provider(provider)
        knowledge_sources = []
        if search_knowledge_base:
            if self.db is None:
                raise ValueError("Database session is required for knowledge base search.")
            knowledge_search = KnowledgeSearchService(self.db)
            knowledge_sources = await knowledge_search.search_knowledge_base(question, k=k)

        prompt = self._build_prompt(question, knowledge_sources, system_prompt)
        yield {
            "type": "metadata",
            "data": {
                "sources": [
                    {
                        "document_id": source.get("document_id"),
                        "chunk_index": source.get("chunk_index"),
                        "snippet": source.get("text", "")[:240],
                    }
                    for source in knowledge_sources
                ],
                "source_count": len(knowledge_sources),
            },
        }

        # Stream tokens and also accumulate final answer; cache final result
        answer = ""
        async for chunk in provider_instance.stream(
            prompt=prompt,
            model=model,
            system=system_prompt,
        ):
            text = str(chunk or "")
            if text:
                answer += text
                yield {"type": "token", "content": text}

        # Cache final answer for identical prompt
        try:
            model_name = model or getattr(_settings, "FAST_RAG_MODEL", "phi3:mini")
            cache_key = key_for_text("prompt", model_name, prompt)
            ttl = getattr(_settings, "CACHE_TTL_SECONDS", 300)
            set_json(cache_key, answer, ex=ttl)
        except Exception:
            pass

        yield {
            "type": "done",
            "answer": answer,
            "sources": [
                {
                    "document_id": source.get("document_id"),
                    "chunk_index": source.get("chunk_index"),
                    "snippet": source.get("text", "")[:240],
                }
                for source in knowledge_sources
            ],
            "used_knowledge_base": bool(knowledge_sources),
        }

    def _build_prompt(
        self,
        question: str,
        sources: list[dict],
        system_prompt: Optional[str],
    ) -> str:
        if sources:
            context_text = "\n\n".join(
                [f"[doc:{source.get('document_id')}#{source.get('chunk_index')}] {source.get('text')}" for source in sources]
            )
            return (
                f"User question: {question}\n\n"
                f"Knowledge Base Context:\n{context_text}\n\n"
                f"Answer using the provided documents first. If the answer is not contained in the documents, say so clearly and then add a short general-knowledge response. Always cite the documents as [doc:id#chunk]."
            )

        return (
            f"User question: {question}\n\n"
            f"Please answer the question directly and clearly. If the question cannot be answered from a knowledge base, say so clearly and provide a helpful general answer."
        )
