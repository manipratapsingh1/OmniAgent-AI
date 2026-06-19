from typing import List
from app.llm.ollama_client import ollama
from app.config import get_settings

import structlog

_settings = get_settings()
_log = structlog.get_logger("embeddings")


async def embed_texts(texts: List[str]) -> List[List[float]]:
    """Embed a list of texts with Redis caching per-text+model to avoid duplicate embeddings.
    
    Gracefully degrades if Redis is unavailable — embeddings still work, just without caching.
    """
    if not texts:
        return []

    model = getattr(_settings, "OLLAMA_EMBED_MODEL", "nomic-embed-text")
    
    # Try to use cache, but don't fail if Redis is down
    cache_available = True
    try:
        from app.cache import key_for_text, get_json, set_json
    except Exception:
        cache_available = False

    cached = []
    missing_indexes = []
    missing_texts = []

    # Try to retrieve cached embeddings per text
    if cache_available:
        for i, t in enumerate(texts):
            try:
                key = key_for_text("embed", model, t)
                v = get_json(key)
                if v is not None:
                    cached.append((i, v))
                    continue
            except Exception:
                pass  # Redis down, skip cache for this text
            missing_indexes.append(i)
            missing_texts.append(t)
    else:
        # No cache: embed everything
        missing_indexes = list(range(len(texts)))
        missing_texts = list(texts)

    results = [None] * len(texts)
    # Fill in cached
    for idx, emb in cached:
        results[idx] = emb

    # Compute missing embeddings in batch if needed
    if missing_texts:
        _log.info(
            "embed.computing",
            total=len(texts),
            cached=len(cached),
            to_compute=len(missing_texts),
            model=model,
        )
        new_vectors = await ollama.embed(missing_texts)
        # ensure sizes match
        if not new_vectors or len(new_vectors) != len(missing_texts):
            raise RuntimeError(
                f"Embedding provider returned {len(new_vectors) if new_vectors else 0} vectors "
                f"for {len(missing_texts)} texts"
            )

        # store and fill
        for mi, vec in enumerate(new_vectors):
            orig_idx = missing_indexes[mi]
            results[orig_idx] = vec
            # cache the embedding (non-blocking, skip on failure)
            if cache_available:
                try:
                    key = key_for_text("embed", model, texts[orig_idx])
                    ttl = getattr(_settings, "CACHE_TTL_SECONDS", 3600)
                    set_json(key, vec, ex=ttl)
                except Exception:
                    pass  # Redis down, skip caching

    # All results should be populated
    return results