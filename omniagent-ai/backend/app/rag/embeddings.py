from typing import List
from app.llm.ollama_client import ollama
from app.cache import key_for_text, get_json, set_json
from app.config import get_settings


_settings = get_settings()


async def embed_texts(texts: List[str]) -> List[List[float]]:
    """Embed a list of texts with Redis caching per-text+model to avoid duplicate embeddings."""
    if not texts:
        return []

    model = getattr(_settings, "OLLAMA_EMBED_MODEL", "nomic-embed-text")
    cached = []
    missing_indexes = []
    missing_texts = []

    # Try to retrieve cached embeddings per text
    for i, t in enumerate(texts):
        key = key_for_text("embed", model, t)
        v = get_json(key)
        if v is not None:
            cached.append((i, v))
        else:
            missing_indexes.append(i)
            missing_texts.append(t)

    results = [None] * len(texts)
    # Fill in cached
    for idx, emb in cached:
        results[idx] = emb

    # Compute missing embeddings in batch if needed
    if missing_texts:
        new_vectors = await ollama.embed(missing_texts)
        # ensure sizes match
        if not new_vectors or len(new_vectors) != len(missing_texts):
            raise RuntimeError("Embedding provider returned unexpected result")

        # store and fill
        for mi, vec in enumerate(new_vectors):
            orig_idx = missing_indexes[mi]
            results[orig_idx] = vec
            # cache the embedding
            try:
                key = key_for_text("embed", model, texts[orig_idx])
                # store as JSON; set TTL from settings if available
                ttl = getattr(_settings, "CACHE_TTL_SECONDS", 3600)
                set_json(key, vec, ex=ttl)
            except Exception:
                pass

    # All results should be populated
    return results