"""
Cross-encoder-style reranking using multi-signal fusion.
Combines BM25, vector score, metadata relevance, and position bias.
No external ML model required — lightweight and production-safe.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

import structlog

from app.rag.hybrid_search import bm25_score

log = structlog.get_logger("reranker")

# Weights for multi-signal fusion (sum to 1.0)
_W_VECTOR = 0.40
_W_BM25 = 0.35
_W_METADATA = 0.15
_W_POSITION = 0.10


def _metadata_score(chunk: Dict[str, Any], query: str) -> float:
    """Score based on metadata field matches."""
    query_lower = query.lower()
    score = 0.0

    section = (chunk.get("section") or "").lower()
    if section and any(w in section for w in query_lower.split()[:5]):
        score += 0.5

    filename = (chunk.get("filename") or chunk.get("document_name") or "").lower()
    if filename and any(w in filename for w in query_lower.split()[:5]):
        score += 0.3

    page = chunk.get("page_number")
    if page is not None and page <= 3:
        score += 0.1  # Slight boost for early pages

    return min(score, 1.0)


def rerank_chunks(
    chunks: List[Dict[str, Any]],
    query: str,
    top_k: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """
    Rerank retrieved chunks using multi-signal cross-encoder-style fusion.
    Updates each chunk's 'score' and adds 'rerank_score' field.
    """
    if not chunks:
        return []

    query = query.strip()
    if not query:
        return chunks[:top_k] if top_k else chunks

    scored = []
    for rank, chunk in enumerate(chunks):
        text = chunk.get("text") or ""
        vector_score = float(chunk.get("score", 0.0))
        bm25 = bm25_score(query, text)
        # Normalize BM25 to 0-1 range (approximate)
        bm25_norm = min(bm25 / 10.0, 1.0)
        meta = _metadata_score(chunk, query)
        position = 1.0 / (1.0 + rank * 0.1)  # Decay by original rank

        # Irrelevant chunk check: if both vector similarity and text overlap are near-zero,
        # do not boost with position or metadata bias
        if vector_score < 0.15 and bm25_norm < 0.05:
            rerank_score = 0.05
        else:
            rerank_score = (
                _W_VECTOR * min(vector_score, 1.0)
                + _W_BM25 * bm25_norm
                + _W_METADATA * meta
                + _W_POSITION * position
            )

        entry = dict(chunk)
        entry["rerank_score"] = round(rerank_score, 4)
        entry["score"] = rerank_score
        entry["bm25_score"] = bm25
        scored.append(entry)

    scored.sort(key=lambda x: x["rerank_score"], reverse=True)

    log.debug(
        "reranker.complete",
        input_count=len(chunks),
        output_count=top_k or len(scored),
        top_score=scored[0]["rerank_score"] if scored else 0,
    )

    if top_k:
        return scored[:top_k]
    return scored


def compute_mrr(relevant_ranks: List[int]) -> float:
    """Mean Reciprocal Rank for RAG evaluation."""
    if not relevant_ranks:
        return 0.0
    return sum(1.0 / r for r in relevant_ranks) / len(relevant_ranks)


def compute_precision_at_k(relevant_in_top_k: int, k: int) -> float:
    """Precision@K for RAG evaluation."""
    if k <= 0:
        return 0.0
    return relevant_in_top_k / k


def compute_ndcg_at_k(relevances: List[float], k: int) -> float:
    """Normalized Discounted Cumulative Gain at K."""
    if not relevances or k <= 0:
        return 0.0

    relevances = relevances[:k]
    dcg = relevances[0]
    for i in range(1, len(relevances)):
        dcg += relevances[i] / __import__("math").log2(i + 2)

    ideal = sorted(relevances, reverse=True)
    idcg = ideal[0]
    for i in range(1, len(ideal)):
        idcg += ideal[i] / __import__("math").log2(i + 2)

    return dcg / idcg if idcg > 0 else 0.0
