from __future__ import annotations

import asyncio
from typing import AsyncIterator, List, Optional

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import get_settings
from app.utils.resilience import breakers

_settings = get_settings()


class OllamaClient:
    def __init__(self, base_url: Optional[str] = None):
        self.base_url = (base_url or _settings.OLLAMA_BASE_URL).rstrip("/")
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=float(_settings.OLLAMA_GENERATE_TIMEOUT),
        )
        self._embed_client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=float(_settings.OLLAMA_EMBED_TIMEOUT),
        )

    async def aclose(self) -> None:
        await self._client.aclose()
        await self._embed_client.aclose()

    async def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        system: Optional[str] = None,
        images: Optional[List[str]] = None,
    ) -> str:
        return await breakers["ollama"].call(
            self._generate_raw,
            prompt,
            model,
            system,
            images,
        )

    async def _generate_raw(
        self,
        prompt: str,
        model: Optional[str],
        system: Optional[str],
        images: Optional[List[str]],
    ) -> str:
        import structlog

        log = structlog.get_logger("ollama")

        try:
            payload = {
                "model": model or _settings.OLLAMA_DEFAULT_MODEL,
                "prompt": prompt,
                "system": system or "",
                "stream": False,
            }
            if images:
                payload["images"] = images

            r = await self._client.post("/api/generate", json=payload)
            r.raise_for_status()
            return r.json().get("response", "").strip()

        except Exception as e:
            log.error("ollama.generate.failed", error=str(e))
            raise

    async def stream(
        self,
        prompt: str,
        model: Optional[str] = None,
        system: Optional[str] = None,
        images: Optional[List[str]] = None,
    ) -> AsyncIterator[str]:
        payload = {
            "model": model or _settings.OLLAMA_DEFAULT_MODEL,
            "prompt": prompt,
            "system": system or "",
            "stream": True,
        }
        if images:
            payload["images"] = images

        async with self._client.stream("POST", "/api/generate", json=payload) as r:
            r.raise_for_status()

            async for line in r.aiter_lines():
                if not line:
                    continue

                try:
                    import orjson

                    obj = orjson.loads(line)
                except Exception:
                    continue

                if "response" in obj:
                    yield obj["response"]
                if obj.get("done"):
                    break

    async def is_healthy(self) -> bool:
        """Connection health check method"""
        try:
            r = await self._client.get("/api/tags", timeout=2.0)
            return r.status_code == 200
        except Exception:
            return False

    async def embed(self, texts: List[str], model: Optional[str] = None) -> List[List[float]]:
        import structlog
        import random

        log = structlog.get_logger("ollama")
        m = model or _settings.OLLAMA_EMBED_MODEL

        log.info("embed.start", text_count=len(texts), model=m)
        log.info("embed.circuit_breaker_status", state=breakers["ollama"].state.value, failure_count=breakers["ollama"].failure_count)

        out: List[List[float]] = []
        embedding_dim: Optional[int] = None

        for i, text in enumerate(texts):
            if not text or not text.strip():
                log.warning("embed.skip_empty", index=i)
                if embedding_dim is None:
                    embedding_dim = 768
                out.append([0.0] * embedding_dim)
                continue

            # We define a helper that makes the HTTP request to Ollama
            async def _embed_single() -> List[float]:
                r = await self._embed_client.post(
                    "/api/embeddings",
                    json={"model": m, "prompt": text[:4000]},
                )
                r.raise_for_status()
                embedding = r.json().get("embedding")
                if not embedding:
                    raise ValueError("Ollama returned an empty embedding list")
                return embedding

            max_retries = 3
            success = False
            for attempt in range(max_retries):
                try:
                    # Execute within circuit breaker
                    embedding = await breakers["ollama"].call(_embed_single)

                    if embedding_dim is None:
                        embedding_dim = len(embedding)
                        log.info("embed.dimension_detected", dimension=embedding_dim, model=m)

                    out.append(embedding)
                    success = True
                    if (i + 1) % 5 == 0:
                        log.info("embed.progress", completed=i + 1, total=len(texts))
                    break

                except Exception as e:
                    # Exponential backoff with jitter: wait_time = base * 2^attempt + jitter
                    base_wait = 1.0
                    jitter = random.uniform(0.1, 0.5)
                    wait_time = (base_wait * (2 ** attempt)) + jitter
                    
                    log.warning(
                        "embed.error_retry",
                        index=i,
                        attempt=attempt + 1,
                        max_attempts=max_retries,
                        wait_time=round(wait_time, 2),
                        error=str(e),
                    )
                    if attempt == max_retries - 1:
                        # If we exhaust all retries, do not crash the whole batch if we already have some embeddings.
                        # Instead, pad with a zero vector of correct dimension so partial results can proceed.
                        log.error("embed.failed_all_retries", index=i, error=str(e))
                        if embedding_dim is None:
                            embedding_dim = 768
                        out.append([0.0] * embedding_dim)
                    else:
                        await asyncio.sleep(wait_time)

        log.info("embed.complete", count=len(out), dimension=embedding_dim)
        return out

    async def list_models(self) -> List[str]:
        try:
            r = await self._client.get("/api/tags")
            r.raise_for_status()
            return [m["name"] for m in r.json().get("models", [])]
        except Exception:
            return [_settings.OLLAMA_DEFAULT_MODEL]


ollama = OllamaClient()