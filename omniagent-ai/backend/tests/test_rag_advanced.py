"""Advanced RAG tests — query rewriting, reranking, evaluation metrics."""
import pytest
from app.rag.query_rewriter import extract_keywords, rewrite_query, expand_query_with_synonyms
from app.rag.reranker import (
    rerank_chunks,
    compute_mrr,
    compute_precision_at_k,
    compute_ndcg_at_k,
)
from app.utils.context_compression import compress_context, deduplicate_chunks


class TestQueryRewriter:
    def test_extract_keywords(self):
        keywords = extract_keywords("What is machine learning and deep learning?")
        assert "machine" in keywords
        assert "learning" in keywords
        assert "what" not in keywords

    def test_rewrite_generates_variants(self):
        variants = rewrite_query("What is artificial intelligence?")
        assert len(variants) >= 1
        assert variants[0] == "What is artificial intelligence?"

    def test_rewrite_empty_query(self):
        assert rewrite_query("") == []

    def test_expand_synonyms(self):
        expanded = expand_query_with_synonyms("Explain RAG systems")
        assert "retrieval" in expanded.lower()

    def test_expand_no_synonyms(self):
        original = "Explain photosynthesis"
        assert expand_query_with_synonyms(original) == original


class TestReranker:
    def test_rerank_by_relevance(self):
        chunks = [
            {"text": "unrelated weather forecast sunny", "score": 0.9, "document_id": 1, "chunk_index": 0},
            {"text": "machine learning neural networks deep learning", "score": 0.5, "document_id": 2, "chunk_index": 0},
        ]
        ranked = rerank_chunks(chunks, "machine learning", top_k=2)
        assert ranked[0]["document_id"] == 2

    def test_rerank_empty(self):
        assert rerank_chunks([], "query") == []

    def test_rerank_adds_score_field(self):
        chunks = [{"text": "test content", "score": 0.5, "document_id": 1, "chunk_index": 0}]
        ranked = rerank_chunks(chunks, "test")
        assert "rerank_score" in ranked[0]

    def test_metadata_boost(self):
        chunks = [
            {"text": "some content about taxes", "score": 0.5, "document_id": 1, "chunk_index": 0},
            {
                "text": "other content",
                "score": 0.5,
                "document_id": 2,
                "chunk_index": 0,
                "section": "Tax Regulations",
            },
        ]
        ranked = rerank_chunks(chunks, "tax regulations")
        assert ranked[0]["document_id"] == 2


class TestRAGEvaluationMetrics:
    def test_mrr(self):
        assert compute_mrr([1, 3]) == pytest.approx(0.667, abs=0.01)

    def test_mrr_empty(self):
        assert compute_mrr([]) == 0.0

    def test_precision_at_k(self):
        assert compute_precision_at_k(2, 5) == 0.4

    def test_ndcg_at_k(self):
        ndcg = compute_ndcg_at_k([3.0, 2.0, 1.0, 0.0], k=4)
        assert 0.0 < ndcg <= 1.0


class TestContextCompression:
    def test_compress_truncates(self):
        chunks = [
            {"text": "a" * 5000, "score": 0.9},
            {"text": "b" * 2000, "score": 0.8},
        ]
        compressed = compress_context(chunks, max_total_chars=6000)
        total = sum(len(c.get("text", "")) for c in compressed)
        assert total <= 6100  # Allow for truncation marker

    def test_compress_empty(self):
        assert compress_context([]) == []

    def test_deduplicate(self):
        chunks = [
            {"text": "machine learning is great for AI tasks", "score": 0.9},
            {"text": "machine learning is great for AI tasks and more", "score": 0.8},
        ]
        deduped = deduplicate_chunks(chunks, similarity_threshold=0.5)
        assert len(deduped) == 1

    def test_deduplicate_single(self):
        chunks = [{"text": "unique content", "score": 0.5}]
        assert deduplicate_chunks(chunks) == chunks
