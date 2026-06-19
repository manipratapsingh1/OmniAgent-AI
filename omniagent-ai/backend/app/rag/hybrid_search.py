"""
Hybrid search combining vector similarity and BM25-style keyword scoring.
Uses Reciprocal Rank Fusion (RRF) to merge ranked result lists.
"""
from __future__ import annotations

import math
import re
from typing import Any, Dict, List, Optional

import structlog

log = structlog.get_logger("hybrid_search")

RRF_K = 60  # Standard RRF constant


def _tokenize(text: str) -> List[str]:
    return [t.lower() for t in re.split(r"\W+", text) if len(t) >= 2]


def bm25_score(query: str, document: str, avg_dl: float = 500.0, k1: float = 1.5, b: float = 0.75) -> float:
    """Compute a BM25-like relevance score for a query-document pair."""
    if not query or not document:
        return 0.0

    query_terms = _tokenize(query)
    if not query_terms:
        return 0.0

    doc_terms = _tokenize(document)
    if not doc_terms:
        return 0.0

    doc_len = len(doc_terms)
    term_freq: Dict[str, int] = {}
    for term in doc_terms:
        term_freq[term] = term_freq.get(term, 0) + 1

    score = 0.0
    for term in set(query_terms):
        tf = term_freq.get(term, 0)
        if tf == 0:
            continue
        # Simplified IDF (assume moderate corpus)
        idf = math.log(1 + 100 / (1 + tf))
        numerator = tf * (k1 + 1)
        denominator = tf + k1 * (1 - b + b * (doc_len / avg_dl))
        score += idf * (numerator / denominator)

    return score


def reciprocal_rank_fusion(
    ranked_lists: List[List[Dict[str, Any]]],
    id_key: str = "chunk_key",
    k: int = RRF_K,
) -> List[Dict[str, Any]]:
    """
    Merge multiple ranked result lists using Reciprocal Rank Fusion.
    Each result dict must have a unique id_key for deduplication.
    """
    scores: Dict[str, float] = {}
    items: Dict[str, Dict[str, Any]] = {}

    for ranked in ranked_lists:
        for rank, item in enumerate(ranked):
            key = item.get(id_key) or f"{item.get('document_id')}:{item.get('chunk_index')}"
            scores[key] = scores.get(key, 0.0) + 1.0 / (k + rank + 1)
            if key not in items:
                items[key] = item

    fused = []
    for key, rrf_score in sorted(scores.items(), key=lambda x: x[1], reverse=True):
        entry = dict(items[key])
        entry["rrf_score"] = rrf_score
        entry["score"] = rrf_score
        fused.append(entry)

    return fused


def hybrid_merge(
    vector_results: List[Dict[str, Any]],
    keyword_results: List[Dict[str, Any]],
    query: str,
    top_k: int = 10,
) -> List[Dict[str, Any]]:
    """
    Fuse vector and keyword search results with BM25 re-scoring.
    Returns deduplicated, re-ranked results.
    """
    for item in vector_results:
        item["chunk_key"] = f"{item.get('document_id')}:{item.get('chunk_index')}"
        item["search_type"] = "vector"

    for item in keyword_results:
        item["chunk_key"] = f"{item.get('document_id')}:{item.get('chunk_index')}"
        item["search_type"] = "keyword"
        text = item.get("text") or ""
        item["bm25_score"] = bm25_score(query, text)

    # Re-rank keyword results by BM25
    keyword_ranked = sorted(keyword_results, key=lambda x: x.get("bm25_score", 0), reverse=True)
    vector_ranked = sorted(vector_results, key=lambda x: x.get("score", 0), reverse=True)

    fused = reciprocal_rank_fusion([vector_ranked, keyword_ranked])

    # Apply BM25 boost to fused results
    for item in fused:
        text = item.get("text") or ""
        bm25 = bm25_score(query, text)
        item["bm25_score"] = bm25
        item["score"] = item.get("rrf_score", 0) + bm25 * 0.01

    fused.sort(key=lambda x: x.get("score", 0), reverse=True)
    log.debug(
        "hybrid_search.merged",
        vector_count=len(vector_results),
        keyword_count=len(keyword_results),
        fused_count=len(fused),
    )
    # Cross-encoder-style reranking
    from app.rag.reranker import rerank_chunks
    return rerank_chunks(fused, query, top_k=top_k)


def filter_irrelevant_chunks(
    chunks: List[Dict[str, Any]],
    query: str,
    min_score: float = 0.05,
) -> List[Dict[str, Any]]:
    """Remove chunks with very low relevance scores."""
    if not chunks:
        return []

    filtered = []
    for chunk in chunks:
        text = chunk.get("text") or ""
        score = chunk.get("score", 0)
        bm25 = bm25_score(query, text)
        combined = max(score, bm25 * 0.01)
        if combined >= min_score or bm25 > 0.5:
            chunk["score"] = combined
            filtered.append(chunk)

    return filtered if filtered else chunks[:3]  # Keep top 3 if all filtered out


def assess_retrieval_confidence(chunks: List[Dict[str, Any]]) -> str:
    """Assess overall retrieval confidence: high, medium, low, none."""
    if not chunks:
        return "none"

    top_score = chunks[0].get("score", 0)
    if top_score >= 0.7:
        return "high"
    if top_score >= 0.35:
        return "medium"
    if top_score >= 0.1:
        return "low"
    return "none"
