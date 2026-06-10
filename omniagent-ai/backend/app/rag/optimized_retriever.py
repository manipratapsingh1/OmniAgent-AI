"""
Optimized RAG retriever with parallel retrieval and result caching
"""
import asyncio
from typing import List, Dict, Any, Optional
import structlog
from app.utils.performance import measure_time
from app import metrics as app_metrics
from time import time

from app.rag.embeddings import embed_texts

log = structlog.get_logger("rag_retriever")


class OptimizedRAGRetriever:
    """Fast RAG retriever with caching and optimization"""

    def __init__(self, chroma_collection):
        self.chroma = chroma_collection
        self._query_cache: Dict[str, list] = {}

    @measure_time("rag.retrieve")
    async def retrieve(self, query: str, limit: int = 5, use_cache: bool = True, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Retrieve relevant documents with optional caching
        
        Args:
            query: Search query
            limit: Max results to return (optimized default)
            use_cache: Whether to use cached results for identical queries
        
        Returns:
            List of relevant document chunks
        """
        # include filters in cache key to avoid cross-contamination
        cache_key = f"{query}:{limit}:{repr(filters)}"
        if use_cache and cache_key in self._query_cache:
            log.debug("rag.cache_hit", query=query)
            return self._query_cache[cache_key]

        start = time()
        try:
            # increment counter
            app_metrics.RETRIEVAL_REQUESTS.labels(endpoint="optimized_retrieve").inc()
            # Generate embedding asynchronously using project's embed_texts
            vecs = await embed_texts([query])
            if not vecs:
                log.warning("rag.embed_empty", query=query)
                return []

            embedding = vecs[0]

            # Query Chroma with timeout
            results = await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(
                    None, self._query_chroma, embedding, limit, filters
                ),
                timeout=2.0,
            )

            # Cache the results
            self._query_cache[cache_key] = results
            elapsed = time() - start
            app_metrics.RETRIEVAL_LATENCY.labels(endpoint="optimized_retrieve").observe(elapsed)

            log.info("rag.retrieve_success", query=query, results_count=len(results))
            return results

        except asyncio.TimeoutError:
            log.warning("rag.retrieve_timeout", query=query)
            return []
        except Exception as e:
            log.error("rag.retrieve_error", query=query, error=str(e))
            return []
    
    def _query_chroma(self, embedding: list, limit: int, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Query Chroma collection and return scored results"""
        try:
            query_kwargs = {
                "query_embeddings": [embedding],
                "n_results": limit,
                "include": ["documents", "metadatas", "distances"],
            }
            if filters:
                query_kwargs["where"] = filters

            result = self.chroma.query(**query_kwargs)

            if result and result.get("documents") and result["documents"][0]:
                docs = result["documents"][0]
                metas = result["metadatas"][0] if result.get("metadatas") else [{}] * len(docs)
                distances = result.get("distances", [[]])[0] if result.get("distances") else [0] * len(docs)

                # Convert distances to a 0..1 ish score (lower distance -> higher score)
                return [
                    {
                        "text": doc,
                        "document_id": meta.get("document_id"),
                        "chunk_index": meta.get("chunk_index", i),
                        "score": 1.0 - distances[i] if distances and i < len(distances) else 0.0,
                    }
                    for i, (doc, meta) in enumerate(zip(docs, metas))
                ]

            return []
        except Exception as e:
            log.error("chroma.query_error", error=str(e))
            return []
    
    def clear_cache(self) -> None:
        """Clear query cache"""
        self._query_cache.clear()
        log.info("rag.cache_cleared")
    
    def get_cache_stats(self) -> Dict[str, int]:
        """Get cache statistics"""
        return {"cached_queries": len(self._query_cache)}


class BatchRAGRetriever:
    """Retriever optimized for batch queries"""
    
    def __init__(self, base_retriever: OptimizedRAGRetriever):
        self.retriever = base_retriever
    
    async def retrieve_batch(self, queries: List[str], limit: int = 5) -> List[List[Dict[str, Any]]]:
        """
        Retrieve results for multiple queries in parallel
        
        Args:
            queries: List of search queries
            limit: Max results per query
        
        Returns:
            List of result lists
        """
        tasks = [
            self.retriever.retrieve(query, limit, use_cache=True)
            for query in queries
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions
        return [
            r if not isinstance(r, Exception) else []
            for r in results
        ]
