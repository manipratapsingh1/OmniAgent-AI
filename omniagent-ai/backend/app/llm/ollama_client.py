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
        self._client = httpx.AsyncClient(base_url=self.base_url, timeout=60.0)
        self._embed_client = httpx.AsyncClient(base_url=self.base_url, timeout=30.0)

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

    @retry(stop=stop_after_attempt(2), wait=wait_exponential(min=2, max=15))
    async def embed(self, texts: List[str], model: Optional[str] = None) -> List[List[float]]:
        import structlog

        log = structlog.get_logger("ollama")
        m = model or _settings.OLLAMA_EMBED_MODEL

        log.info("embed.start", text_count=len(texts), model=m)

        out: List[List[float]] = []
        embedding_dim: Optional[int] = None

        for i, text in enumerate(texts):
            if not text or not text.strip():
                log.warning("embed.skip_empty", index=i)
                if embedding_dim is None:
                    embedding_dim = 768
                out.append([0.0] * embedding_dim)
                continue

            max_retries = 2

            for attempt in range(max_retries):
                try:
                    r = await self._embed_client.post(
                        "/api/embeddings",
                        json={"model": m, "prompt": text[:4000]},
                    )
                    r.raise_for_status()

                    embedding = r.json().get("embedding")
                    if not embedding:
                        log.error("embed.empty_embedding", index=i, text_length=len(text))
                        if attempt == max_retries - 1:
                            return []
                        continue

                    if embedding_dim is None:
                        embedding_dim = len(embedding)
                        log.info("embed.dimension_detected", dimension=embedding_dim, model=m)

                    out.append(embedding)

                    if (i + 1) % 5 == 0:
                        log.info("embed.progress", completed=i + 1, total=len(texts))

                    break

                except httpx.TimeoutException as e:
                    log.warning(
                        "embed.timeout",
                        index=i,
                        text_length=len(text),
                        attempt=attempt + 1,
                        max_attempts=max_retries,
                        error=str(e),
                    )
                    if attempt == max_retries - 1:
                        raise
                    await asyncio.sleep(2**attempt)

                except Exception as e:
                    log.warning(
                        "embed.error",
                        index=i,
                        text_length=len(text),
                        attempt=attempt + 1,
                        max_attempts=max_retries,
                        error=str(e),
                    )
                    if attempt == max_retries - 1:
                        raise
                    await asyncio.sleep(1)

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