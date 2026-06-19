from typing import Optional, Any
from app.config import get_settings
from .provider import AIProvider
from app.services.ai.provider_registry import build_providers, get_model_router
from .openai_provider import OpenAIProvider
from .ollama_provider import OllamaProvider
from .gemini_provider import GeminiProvider
from .model_router import ModelRouter
from .knowledge_search import KnowledgeSearchService
from app.cache import key_for_text, get_json, set_json


_settings = get_settings()


import structlog

_log = structlog.get_logger("ai_service")

class AIService:
    def __init__(self, db: Optional[Any] = None, provider: Optional[str] = None):
        self.settings = get_settings()
        self.db = db
        self.default_provider = provider or self.settings.DEFAULT_LLM_PROVIDER or "ollama"
        self.providers: dict[str, AIProvider] = build_providers()
        self.router = ModelRouter(self.providers)

    def choose_provider(self, provider_name: Optional[str] = None) -> AIProvider:
        name = provider_name or self.default_provider or "ollama"
        if name in self.providers:
            return self.providers[name]
        return self.providers.get("ollama", OllamaProvider())

    async def get_healthy_provider(self, provider_name: Optional[str] = None) -> AIProvider:
        """Resolve a healthy provider, falling back to other configured and healthy providers if needed."""
        primary_name = provider_name or self.default_provider or "ollama"
        
        # Check primary provider first
        if primary_name in self.providers:
            provider = self.providers[primary_name]
            if await provider.is_healthy():
                return provider
            _log.warning("provider.unhealthy", provider=primary_name, msg="Primary provider is unhealthy. Trying fallback chain.")
            
        # Fallback chain prioritizing configured and healthy ones
        fallbacks = ["ollama", "openai", "anthropic", "gemini", "groq"]
        for name in fallbacks:
            if name != primary_name and name in self.providers:
                provider = self.providers[name]
                if await provider.is_healthy():
                    _log.info("provider.fallback_selected", original=primary_name, fallback=name)
                    return provider
                    
        # Defaults if no healthy provider found
        fallback_default = self.providers.get(primary_name) or self.providers.get("ollama")
        if fallback_default:
            return fallback_default
        return OllamaProvider()

    async def generate(self, prompt: str, provider: Optional[str] = None, **kwargs) -> str:
        p = await self.get_healthy_provider(provider)
        
        # Collision-free cache key: include provider, model, system prompt, and prompt
        model = kwargs.get("model") or getattr(_settings, "FAST_RAG_MODEL", "phi3:mini")
        system_prompt = kwargs.get("system") or ""
        cache_input = f"{p.name}:{model}:{system_prompt}:{prompt}"
        cache_key = key_for_text("prompt_v2", "", cache_input)

        try:
            cached = get_json(cache_key)
            if cached:
                return cached
        except Exception:
            cached = None

        try:
            resp = await p.generate(prompt, **kwargs)
        except Exception as e:
            _log.error("ai_service.generate.failed", provider=p.name, error=str(e), msg="Primary attempt failed. Retrying with ollama.")
            if p.name != "ollama":
                try:
                    ollama_p = self.providers.get("ollama") or OllamaProvider()
                    resp = await ollama_p.generate(prompt, **kwargs)
                except Exception as ollama_err:
                    _log.error("ai_service.emergency_fallback.failed", error=str(ollama_err))
                    raise e
            else:
                raise e

        try:
            ttl = getattr(_settings, "CACHE_TTL_SECONDS", 300)
            set_json(cache_key, resp, ex=ttl)
        except Exception:
            pass

        return resp

    async def stream(self, prompt: str, provider: Optional[str] = None, **kwargs):
        p = await self.get_healthy_provider(provider)
        try:
            async for chunk in p.stream(prompt, **kwargs):
                yield chunk
        except Exception as e:
            _log.error("ai_service.stream.failed", provider=p.name, error=str(e))
            if p.name != "ollama":
                _log.info("ai_service.stream.fallback_to_ollama")
                try:
                    ollama_p = self.providers.get("ollama") or OllamaProvider()
                    async for chunk in ollama_p.stream(prompt, **kwargs):
                        yield chunk
                except Exception as ollama_err:
                    _log.error("ai_service.stream.emergency_fallback.failed", error=str(ollama_err))
                    raise e
            else:
                raise e

    async def embed(self, texts: list[str], provider: Optional[str] = None):
        p = await self.get_healthy_provider(provider)
        try:
            return await p.embed(texts)
        except Exception as e:
            _log.error("ai_service.embed.failed", provider=p.name, error=str(e))
            if p.name != "ollama":
                try:
                    ollama_p = self.providers.get("ollama") or OllamaProvider()
                    return await ollama_p.embed(texts)
                except Exception:
                    raise e
            raise e

    async def query(
        self,
        question: str,
        model: Optional[str] = None,
        provider: Optional[str] = None,
        search_knowledge_base: bool = False,
        k: int = 5,
        system_prompt: Optional[str] = None,
    ) -> dict:
        provider_instance = await self.get_healthy_provider(provider)
        knowledge_sources = []
        if search_knowledge_base:
            if self.db is None:
                raise ValueError("Database session is required for knowledge base search.")
            knowledge_search = KnowledgeSearchService(self.db)
            knowledge_sources = await knowledge_search.search_knowledge_base(question, k=k)

        prompt = self._build_prompt(question, knowledge_sources, system_prompt)
        
        # Check cache
        cache_model = model or getattr(_settings, "FAST_RAG_MODEL", "phi3:mini")
        cache_input = f"{provider_instance.name}:{cache_model}:{system_prompt or ''}:{prompt}"
        cache_key = key_for_text("prompt_v2", "", cache_input)
        try:
            cached = get_json(cache_key)
            if cached:
                return {
                    "answer": cached,
                    "sources": knowledge_sources,
                    "used_knowledge_base": bool(knowledge_sources),
                }
        except Exception:
            pass

        try:
            answer = await provider_instance.generate(
                prompt=prompt,
                model=model,
                system=system_prompt,
            )
        except Exception as e:
            _log.error("ai_service.query.failed", provider=provider_instance.name, error=str(e))
            if provider_instance.name != "ollama":
                ollama_p = self.providers.get("ollama") or OllamaProvider()
                answer = await ollama_p.generate(
                    prompt=prompt,
                    model=model,
                    system=system_prompt,
                )
            else:
                raise e

        try:
            ttl = getattr(_settings, "CACHE_TTL_SECONDS", 300)
            set_json(cache_key, answer, ex=ttl)
        except Exception:
            pass

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
        provider_instance = await self.get_healthy_provider(provider)
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
        try:
            async for chunk in provider_instance.stream(
                prompt=prompt,
                model=model,
                system=system_prompt,
            ):
                text = str(chunk or "")
                if text:
                    answer += text
                    yield {"type": "token", "content": text}
        except Exception as e:
            _log.error("ai_service.stream_query.failed", provider=provider_instance.name, error=str(e))
            if provider_instance.name != "ollama":
                _log.info("ai_service.stream_query.fallback_to_ollama")
                ollama_p = self.providers.get("ollama") or OllamaProvider()
                async for chunk in ollama_p.stream(
                    prompt=prompt,
                    model=model,
                    system=system_prompt,
                ):
                    text = str(chunk or "")
                    if text:
                        answer += text
                        yield {"type": "token", "content": text}
            else:
                raise e

        # Cache final answer for identical prompt
        try:
            cache_model = model or getattr(_settings, "FAST_RAG_MODEL", "phi3:mini")
            cache_input = f"{provider_instance.name}:{cache_model}:{system_prompt or ''}:{prompt}"
            cache_key = key_for_text("prompt_v2", "", cache_input)
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
