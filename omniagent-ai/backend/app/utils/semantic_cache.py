import time
import structlog
from typing import Optional
from app.rag.retriever import get_vector_store
from app.rag.embeddings import embed_texts

log = structlog.get_logger("semantic_cache")


class SemanticCache:
    def __init__(self, distance_threshold: float = 0.15):
        self.distance_threshold = distance_threshold
        self.collection = None
        self._initialized = False

    def _init_collection(self):
        if self._initialized:
            return
        try:
            store = get_vector_store()
            if store and store.client:
                self.collection = store.client.get_or_create_collection("semantic_cache", metadata={"hnsw:space": "cosine"})
                self._initialized = True
        except Exception as e:
            log.warning("semantic_cache.init_failed", error=str(e))

    async def get(self, query: str) -> Optional[str]:
        """Look up query in semantic cache. Returns cached answer string if found."""
        try:
            self._init_collection()
            if not self._initialized or not self.collection:
                return None

            # Generate query embedding
            vecs = await embed_texts([query])
            if not vecs:
                return None

            # Query Chroma for closest match
            results = self.collection.query(
                query_embeddings=[vecs[0]],
                n_results=1
            )

            if not results or not results.get("documents") or not results["documents"][0]:
                return None

            distances = results.get("distances")
            distance = distances[0][0] if distances and len(distances[0]) > 0 else 1.0
            
            if distance <= self.distance_threshold:
                metadatas = results.get("metadatas")
                metadata = metadatas[0][0] if metadatas and len(metadatas[0]) > 0 else {}
                answer = metadata.get("answer")
                log.info("semantic_cache.hit", query=query, distance=distance)
                return answer

            log.info("semantic_cache.miss", query=query, closest_distance=distance)
            return None
        except Exception as e:
            log.warning("semantic_cache.get_error", error=str(e))
            return None

    async def set(self, query: str, answer: str) -> None:
        """Store query and answer in semantic cache."""
        try:
            self._init_collection()
            if not self._initialized or not self.collection:
                return

            vecs = await embed_texts([query])
            if not vecs:
                return

            # Store in collection
            import uuid
            cache_id = str(uuid.uuid4())
            self.collection.add(
                ids=[cache_id],
                embeddings=[vecs[0]],
                documents=[query],
                metadatas=[{"answer": answer, "created_at": time.time()}]
            )
            log.info("semantic_cache.stored", query=query)
        except Exception as e:
            log.warning("semantic_cache.set_error", error=str(e))


# Global singleton
semantic_cache = SemanticCache()
