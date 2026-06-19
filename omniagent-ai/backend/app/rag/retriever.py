from __future__ import annotations

from typing import List, Dict, Any, Optional, Tuple
import re
import time
import asyncio
import structlog

from app.config import get_settings

_settings = get_settings()
log = structlog.get_logger("vector_store")

# Try to use the optimized retriever when available
try:
    from app.rag.optimized_retriever import OptimizedRAGRetriever
except Exception:
    OptimizedRAGRetriever = None


_optimized_retriever = None

def get_optimized_retriever():
    global _optimized_retriever
    if _optimized_retriever is None and OptimizedRAGRetriever is not None:
        try:
            _optimized_retriever = OptimizedRAGRetriever(get_vector_store().collection)
        except Exception:
            _optimized_retriever = None
    return _optimized_retriever


class VectorStore:
    def __init__(self, max_retries: int = 3, retry_delay: float = 1.0) -> None:
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.client = None
        self.collection = None
        self._initialized = False
        self._initialize_with_retry()

    def _initialize_with_retry(self) -> None:
        """Initialize Chroma client with retry logic"""
        for attempt in range(self.max_retries):
            try:
                # import chromadb lazily so the module can be imported without
                # having chromadb installed (useful for test environments)
                try:
                    import chromadb
                    from chromadb.config import Settings as ChromaSettings
                except Exception as ie:
                    raise RuntimeError(
                        "chromadb is not installed or failed to import: " + str(ie)
                    )
                log.info(
                    "vector_store.connecting",
                    host=_settings.CHROMA_HOST,
                    port=_settings.CHROMA_PORT,
                    attempt=attempt + 1,
                    max_retries=self.max_retries,
                )
                self.client = chromadb.HttpClient(
                    host=_settings.CHROMA_HOST,
                    port=_settings.CHROMA_PORT,
                    settings=ChromaSettings(anonymized_telemetry=False),
                )
                # Test connection by attempting to list collections
                _ = self.client.list_collections()
                self.collection = self.client.get_or_create_collection("omniagent", metadata={"hnsw:space": "cosine"})
                self._initialized = True
                log.info(
                    "vector_store.initialized",
                    host=_settings.CHROMA_HOST,
                    port=_settings.CHROMA_PORT,
                    collection_count=len(self.client.list_collections()),
                )
                return
            except Exception as e:
                log.warning(
                    "vector_store.init_attempt_failed",
                    attempt=attempt + 1,
                    error=str(e),
                )
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                else:
                    log.error(
                        "vector_store.init_failed_all_retries",
                        max_retries=self.max_retries,
                        error=str(e),
                    )
                    raise

    def add(
        self,
        ids: List[str],
        embeddings: List[List[float]],
        documents: List[str],
        metadatas: List[Dict[str, Any]],
    ) -> None:
        """Add documents to Chroma with validation"""
        try:
            if not ids or not embeddings or not documents:
                log.warning("vector_store.add.empty_input", ids_count=len(ids or []))
                raise ValueError("Empty input: ids, embeddings, or documents")

            if len(ids) != len(embeddings) or len(ids) != len(documents):
                log.error(
                    "vector_store.add.length_mismatch",
                    ids_count=len(ids),
                    embeddings_count=len(embeddings),
                    documents_count=len(documents),
                )
                raise ValueError(
                    f"Length mismatch: ids={len(ids)}, embeddings={len(embeddings)}, documents={len(documents)}"
                )

            if not self._initialized or not self.collection:
                log.error("vector_store.not_initialized")
                raise RuntimeError("VectorStore not properly initialized")

            log.info(
                "vector_store.add.start",
                count=len(ids),
                embedding_dim=len(embeddings[0]) if embeddings else 0,
            )
            
            self.collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas,
            )
            
            # Verify data was actually stored
            stored_count = self.collection.count()
            log.info(
                "vector_store.add.success",
                count=len(ids),
                total_in_collection=stored_count,
            )
        except Exception as e:
            log.exception(
                "vector_store.add.failed",
                count=len(ids or []),
                error=str(e),
                error_type=type(e).__name__,
            )
            raise

    def query(self, embedding: List[float], k: int, where: Dict[str, Any], timeout: float = 5.0):
        """Query Chroma with validation and timeout protection"""
        try:
            if not embedding:
                log.warning("vector_store.query.empty_embedding")
                return {"documents": [[]], "metadatas": [[]]}

            if not self._initialized or not self.collection:
                log.error("vector_store.not_initialized")
                return {"documents": [[]], "metadatas": [[]]}

            start_time = time.time()
            
            # Format where filter for Chroma logical operators if it contains multiple conditions
            if where and len(where) > 1 and not ("$and" in where or "$or" in where):
                where = {"$and": [{k: v} for k, v in where.items()]}

            result = self.collection.query(
                query_embeddings=[embedding],
                n_results=k,
                where=where,
            )
            
            elapsed = time.time() - start_time
            if elapsed > timeout:
                log.warning(
                    "vector_store.query.slow",
                    k=k,
                    elapsed_ms=elapsed * 1000,
                    timeout_ms=timeout * 1000,
                )
            
            results_count = len(result.get("documents", [[]])[0]) if result.get("documents") else 0
            log.debug(
                "vector_store.query.success",
                k=k,
                results_count=results_count,
                elapsed_ms=elapsed * 1000,
            )
            return result
        except Exception as e:
            log.exception(
                "vector_store.query.failed",
                k=k,
                error=str(e),
                error_type=type(e).__name__,
            )
            # Return empty results on error instead of raising
            return {"documents": [[]], "metadatas": [[]]}


class _LazyVectorStore:
    """
    Lazy proxy so `from app.rag.retriever import vector_store` still works,
    but Chroma is not initialized until add/query is actually called.
    """

    def __init__(self) -> None:
        self._store: Optional[VectorStore] = None

    def _get_store(self) -> VectorStore:
        if self._store is None:
            self._store = VectorStore()
        return self._store

    def add(
        self,
        ids: List[str],
        embeddings: List[List[float]],
        documents: List[str],
        metadatas: List[Dict[str, Any]],
    ) -> None:
        self._get_store().add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
        )

    def query(self, embedding: List[float], k: int, where: Dict[str, Any], timeout: float = 5.0):
        return self._get_store().query(
            embedding=embedding,
            k=k,
            where=where,
            timeout=timeout,
        )


# This keeps old imports working:
# from app.rag.retriever import vector_store
vector_store = _LazyVectorStore()


def get_vector_store() -> VectorStore:
    """
    Optional explicit accessor if you want to use the real store directly.
    """
    return vector_store._get_store()


def add_documents(
    ids: List[str],
    embeddings: List[List[float]],
    documents: List[str],
    metadatas: List[Dict[str, Any]],
) -> None:
    """
    Add documents to Chroma safely.
    """
    vector_store.add(
        ids=ids,
        embeddings=embeddings,
        documents=documents,
        metadatas=metadatas,
    )


def query_vectors(
    embedding: List[float],
    k: int,
    where: Dict[str, Any],
    timeout: float = 5.0,
):
    """
    Query Chroma safely with timeout protection.
    """
    # Ask underlying vector store for distances and metadatas where supported
    try:
        return vector_store.query(
            embedding=embedding,
            k=k,
            where=where,
            timeout=timeout,
        )
    except Exception:
        return {"documents": [[]], "metadatas": [[]], "distances": [[]]}


def _keyword_search_fallback(
    db,
    query: str,
    k: int,
    filters: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """
    Fallback to a lightweight keyword search over document chunks when vector search returns no results.
    """
    if not db or not query or not query.strip():
        return []

    try:
        from sqlmodel import select, or_, and_
        from app.models.document import Document, DocumentChunk

        tokens = [token for token in re.split(r"\W+", query) if len(token) >= 3]
        if not tokens:
            tokens = [query.strip()]

        keyword_clauses = [DocumentChunk.text.ilike(f"%{token}%") for token in tokens]
        query_filters = [Document.id == DocumentChunk.document_id]

        if filters:
            if filters.get("user_id") is not None:
                query_filters.append(Document.user_id == filters["user_id"])
            if filters.get("document_id") is not None:
                query_filters.append(DocumentChunk.document_id == filters["document_id"])
            if filters.get("status") is not None:
                query_filters.append(Document.status == filters["status"])
            if filters.get("is_knowledge_base") is not None:
                query_filters.append(Document.is_knowledge_base == filters["is_knowledge_base"])

        statement = select(DocumentChunk, Document).where(
            and_(
                *query_filters,
                or_(*keyword_clauses),
            )
        ).limit(k)

        rows = db.exec(statement).all()
        results = []
        for chunk, document in rows:
            results.append({
                "text": chunk.text,
                "document_id": chunk.document_id,
                "chunk_index": chunk.chunk_index,
                "score": 0.1,
                "distance": 1.0,
            })
        return results
    except Exception as e:
        log.warning("retrieve.keyword_fallback.failed", error=str(e))
        return []


async def retrieve(
    user_id: Optional[int],
    query: str,
    k: int = 4,
    filters: Optional[Dict[str, Any]] = None,
    db: Optional[Any] = None,
) -> List[Dict[str, Any]]:
    """
    Retrieve relevant context chunks for a query.
    """
    try:
        # Prefer optimized retriever if available
        where: Dict[str, Any] = {}
        is_kb = filters and filters.get("is_knowledge_base")
        if user_id is not None and not is_kb:
            where["user_id"] = int(user_id)
        if filters:
            # Ensure filter values are Chroma-compatible types
            for fk, fv in filters.items():
                if isinstance(fv, bool):
                    where[fk] = fv
                elif isinstance(fv, int):
                    where[fk] = int(fv)
                elif isinstance(fv, float):
                    where[fk] = float(fv)
                else:
                    where[fk] = str(fv) if fv is not None else fv

        # Simple query-result caching: check Redis for previous results
        try:
            from app.cache import key_for_text, get_json, set_json
            cache_model = getattr(_settings, "FAST_RAG_MODEL", "phi3:mini")
            cache_text = f"user:{user_id}|q:{query}|k:{k}|filters:{filters}"
            cache_key = key_for_text("query", cache_model, cache_text)
            cache_val = get_json(cache_key)
            if cache_val:
                log.info("retrieve.cache.hit", user_id=user_id, query_len=len(query), k=k)
                return cache_val
        except Exception:
            cache_val = None

        log.info("retrieve.start", user_id=user_id, query_len=len(query), k=k, filters=filters)

        try:
            optimized = get_optimized_retriever()
            if optimized:
                # instrument optimized path
                from app import metrics as app_metrics

                app_metrics.RETRIEVAL_REQUESTS.labels(endpoint="optimized_retrieve").inc()
                t0 = time.time()

                results = await optimized.retrieve(query=query, limit=k, use_cache=True, filters=where)

                elapsed = time.time() - t0
                app_metrics.RETRIEVAL_LATENCY.labels(endpoint="optimized_retrieve").observe(elapsed)

                if results:
                    # normalized output
                    out = [
                        {
                            "text": r.get("text"),
                            "document_id": r.get("document_id"),
                            "chunk_index": r.get("chunk_index"),
                            "score": r.get("score", 0),
                            "distance": r.get("distance", 0.0),
                            "page_number": r.get("page_number"),
                            "section": r.get("section"),
                            "filename": r.get("filename"),
                        }
                        for r in results
                    ]
                    log.info(
                        "retrieve.success.optimized",
                        user_id=user_id,
                        results=len(out),
                        elapsed_ms=int(elapsed * 1000),
                        top_score=out[0]["score"] if out else 0,
                    )
                    return out
                else:
                    log.info("retrieve.optimized_empty", user_id=user_id, query=query)
        except Exception as e:
            log.warning("retrieve.optimized_failed", error=str(e))

        # Fallback: generate embedding and query vector store directly
        from app.rag.embeddings import embed_texts
        from app.llm.ollama_client import ollama

        log.info("retrieve.embedding_query", query_len=len(query))
        vecs = await embed_texts([query])
        if not vecs:
            log.warning("retrieve.no_embeddings", query=query)
            return []

        log.info("retrieve.query_vector_created", embedding_dim=len(vecs[0]) if vecs else 0)

        # instrument fallback retrieval
        from app import metrics as app_metrics
        app_metrics.RETRIEVAL_REQUESTS.labels(endpoint="fallback_retrieve").inc()
        t0 = time.time()

        try:
            res = query_vectors(
                embedding=vecs[0],
                k=k,
                where=where,
            )
        except Exception as qe:
            log.warning("retrieve.vector_query_failed", error=str(qe))
            res = {"documents": [[]], "metadatas": [[]], "distances": [[]]}

        elapsed = time.time() - t0
        app_metrics.RETRIEVAL_LATENCY.labels(endpoint="fallback_retrieve").observe(elapsed)

        out: List[Dict[str, Any]] = []
        docs = (res.get("documents") or [[]])[0]
        metas = (res.get("metadatas") or [[]])[0]
        distances = (res.get("distances") or [[]])[0]

        log.info(
            "retrieve.vector_query_complete",
            results_count=len(docs),
            elapsed_ms=int(elapsed * 1000),
        )

        for i, (text, meta) in enumerate(zip(docs, metas)):
            dist = distances[i] if i < len(distances) else 0.0
            if dist < 0.0:
                score = 1.0
            elif dist <= 2.0:
                score = 1.0 - dist
            else:
                score = 1.0 / (1.0 + dist / 10.0)
            # small recency boost if metadata contains timestamp
            try:
                if meta and meta.get("created_at"):
                    # assume ISO timestamp - newer => small boost
                    from datetime import datetime, timezone

                    created = datetime.fromisoformat(meta.get("created_at"))
                    age_seconds = (datetime.now(timezone.utc) - created).total_seconds()
                    # boost up to +0.1 for very recent docs
                    recency_boost = max(0.0, 0.1 - min(age_seconds / (60 * 60 * 24 * 30), 0.1))
                    score += recency_boost
            except Exception:
                pass

            result = {
                "text": text,
                "document_id": meta.get("document_id"),
                "chunk_index": meta.get("chunk_index"),
                "score": score,
                "distance": distances[i] if i < len(distances) else 0.0,
                "page_number": meta.get("page_number"),
                "section": meta.get("section"),
                "filename": meta.get("filename"),
            }
            out.append(result)
            
            log.debug(
                "retrieve.result",
                rank=i + 1,
                doc_id=result["document_id"],
                chunk_idx=result["chunk_index"],
                score=result["score"],
                distance=result["distance"],
                text_len=len(text) if text else 0,
            )

        # Sort by score desc
        out.sort(key=lambda x: x.get("score", 0), reverse=True)

        # Hybrid search: fuse vector results with BM25 keyword results when DB available
        if db is not None and out:
            try:
                from app.rag.hybrid_search import hybrid_merge, filter_irrelevant_chunks
                keyword_results = _keyword_search_fallback(db, query, k, where)
                if keyword_results:
                    out = hybrid_merge(out, keyword_results, query, top_k=k)
                    out = filter_irrelevant_chunks(out, query)
                    log.info(
                        "retrieve.hybrid_merged",
                        user_id=user_id,
                        vector_count=len(docs),
                        keyword_count=len(keyword_results),
                        fused_count=len(out),
                    )
            except Exception as e:
                log.warning("retrieve.hybrid_merge_failed", error=str(e))

        log.info(
            "retrieve.success.fallback",
            user_id=user_id,
            results=len(out),
            top_score=out[0]["score"] if out else 0,
            elapsed_ms=int(elapsed * 1000),
        )

        # Lightweight BM25-based reranking (replaces slow Ollama-based reranking)
        # The Ollama reranking was making sequential API calls per chunk and causing
        # massive latency + contention with generation. BM25 reranking is instant.
        try:
            from app.rag.hybrid_search import bm25_score
            for item in out:
                text = item.get("text") or ""
                bm25 = bm25_score(query, text)
                # Blend vector score with BM25 for better relevance
                item["score"] = item.get("score", 0) * 0.7 + min(bm25 * 0.01, 0.3)
            out.sort(key=lambda x: x.get("score", 0), reverse=True)
        except Exception:
            pass

        if (not out or (out and out[0].get("score", 0) < 0.2)) and db is not None:
            fallback = _keyword_search_fallback(db, query, k, where)
            if fallback:
                log.info(
                    "retrieve.keyword_fallback",
                    user_id=user_id,
                    query=query,
                    fallback_count=len(fallback),
                )
                # cache fallback results
                try:
                    from app.cache import key_for_text, set_json
                    cache_model = getattr(_settings, "FAST_RAG_MODEL", "phi3:mini")
                    cache_text = f"user:{user_id}|q:{query}|k:{k}|filters:{filters}"
                    cache_key = key_for_text("query", cache_model, cache_text)
                    ttl = getattr(_settings, "CACHE_TTL_SECONDS", 300)
                    set_json(cache_key, fallback, ex=ttl)
                except Exception:
                    pass
                return fallback

        # cache semantic results
        try:
            from app.cache import set_json, key_for_text
            cache_model = getattr(_settings, "FAST_RAG_MODEL", "phi3:mini")
            cache_text = f"user:{user_id}|q:{query}|k:{k}|filters:{filters}"
            cache_key = key_for_text("query", cache_model, cache_text)
            ttl = getattr(_settings, "CACHE_TTL_SECONDS", 300)
            set_json(cache_key, out, ex=ttl)
        except Exception:
            pass

        return out

    except Exception as e:
        log.exception(
            "retrieve.failed",
            user_id=user_id,
            query_len=len(query) if query else 0,
            error=str(e),
        )
        return []