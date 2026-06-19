import pytest
from app.rag.hybrid_search import (
    bm25_score,
    reciprocal_rank_fusion,
    assess_retrieval_confidence
)
from app.rag.reranker import (
    compute_mrr,
    compute_precision_at_k,
    compute_ndcg_at_k
)


def test_bm25_scoring():
    # Identical term match should score high
    score1 = bm25_score("machine learning", "machine learning is a subset of artificial intelligence.")
    score2 = bm25_score("machine learning", "some irrelevant document content.")
    assert score1 > score2
    assert bm25_score("", "content") == 0.0
    assert bm25_score("query", "") == 0.0


def test_reciprocal_rank_fusion():
    list1 = [{"document_id": 1, "chunk_index": 0, "text": "doc1"}]
    list2 = [{"document_id": 1, "chunk_index": 0, "text": "doc1"}]
    
    fused = reciprocal_rank_fusion([list1, list2])
    assert len(fused) == 1
    assert fused[0]["score"] > 0.0


def test_retrieval_confidence():
    assert assess_retrieval_confidence([{"score": 0.85}]) == "high"
    assert assess_retrieval_confidence([{"score": 0.50}]) == "medium"
    assert assess_retrieval_confidence([{"score": 0.20}]) == "low"
    assert assess_retrieval_confidence([{"score": 0.05}]) == "none"
    assert assess_retrieval_confidence([]) == "none"


def test_mrr_evaluation():
    # Reciprocal Rank of first relevant item: rank 2 (index 1 is 2nd rank)
    assert compute_mrr([2]) == 0.5
    assert compute_mrr([1, 4]) == 0.625  # (1.0 + 0.25) / 2
    assert compute_mrr([]) == 0.0


def test_precision_at_k():
    assert compute_precision_at_k(2, 5) == 0.4
    assert compute_precision_at_k(3, 3) == 1.0
    assert compute_precision_at_k(0, 5) == 0.0
    assert compute_precision_at_k(1, 0) == 0.0


def test_ndcg_evaluation():
    # Relevance scores
    assert compute_ndcg_at_k([3, 2, 3, 0], 4) > 0.0
    assert compute_ndcg_at_k([], 5) == 0.0
    assert compute_ndcg_at_k([1], 0) == 0.0
