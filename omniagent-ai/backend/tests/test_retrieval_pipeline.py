"""Retrieval pipeline E2E tests — query → rewrite → hybrid search → rerank → cite."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.rag.retriever import retrieve, _keyword_search_fallback, query_vectors
from app.rag.reranker import rerank_chunks, compute_mrr, compute_precision_at_k, compute_ndcg_at_k
from app.utils.citations import get_citations_with_fallback, validate_citation_accuracy, extract_citations_from_response
from app.services.ai.hybrid_knowledge_engine import HybridKnowledgeEngine, KnowledgeMode, KnowledgeCase


MOCK_CHUNKS = [
    {
        "document_id": 1,
        "chunk_index": 0,
        "text": "Machine learning is a subset of artificial intelligence.",
        "score": 0.85,
        "page_number": 1,
        "section": "Introduction",
    },
    {
        "document_id": 1,
        "chunk_index": 1,
        "text": "Deep learning uses neural networks with many layers.",
        "score": 0.72,
        "page_number": 2,
    },
]


@pytest.mark.asyncio
async def test_retrieve_with_mocked_embeddings(db_session_mock):
    with patch("app.rag.embeddings.embed_texts", new=AsyncMock(return_value=[[0.1] * 8])):
        with patch("app.rag.retriever.query_vectors") as mock_qv:
            with patch("app.rag.retriever.get_optimized_retriever", return_value=None):
                mock_qv.return_value = {
                    "documents": [[c["text"] for c in MOCK_CHUNKS]],
                    "metadatas": [[{"document_id": c["document_id"], "chunk_index": c["chunk_index"]} for c in MOCK_CHUNKS]],
                    "distances": [[0.15, 0.28]],
                }
                results = await retrieve(user_id=1, query="machine learning", k=5, db=db_session_mock)
    assert isinstance(results, list)


def test_keyword_search_fallback(db_session_mock):
    from app.models.document import DocumentChunk

    chunk = MagicMock()
    chunk.document_id = 1
    chunk.chunk_index = 0
    chunk.text = "machine learning algorithms"
    db_session_mock.exec.return_value.all.return_value = [chunk]

    results = _keyword_search_fallback(db_session_mock, "machine learning", k=5, filters=None)
    assert isinstance(results, list)


class TestRetrievalToCitation:
    def test_rerank_improves_relevance_order(self):
        chunks = [
            {"text": "weather forecast sunny", "score": 0.9, "document_id": 2, "chunk_index": 0},
            {"text": "machine learning neural networks", "score": 0.5, "document_id": 1, "chunk_index": 0},
        ]
        ranked = rerank_chunks(chunks, "machine learning", top_k=2)
        assert ranked[0]["document_id"] == 1

    def test_citation_from_answer(self):
        answer = "According to [doc:1#0], machine learning is important."
        sources = MOCK_CHUNKS
        cited, was_cited = get_citations_with_fallback(answer, sources)
        assert was_cited is True
        assert len(cited) >= 1

    def test_citation_validation(self):
        answer = "See [doc:1#0] for details on ML."
        result = validate_citation_accuracy(answer, MOCK_CHUNKS)
        assert result["citations_in_text"] >= 1

    def test_extract_citations_from_response(self):
        answer = "See [doc:1#0] and [doc:1#1] for details."
        citations = extract_citations_from_response(answer)
        assert len(citations) >= 1


class TestHybridRetrievalPipeline:
    @pytest.mark.asyncio
    async def test_hybrid_engine_full_retrieval(self, db_session_mock):
        engine = HybridKnowledgeEngine(db=db_session_mock)

        with patch.object(engine, "_hybrid_retrieve", new=AsyncMock(return_value=MOCK_CHUNKS)):
            with patch.object(engine, "_get_memory_context", new=AsyncMock(return_value=["[memory:fact] User likes ML"])):
                result = await engine.retrieve_and_decide(
                    user_id=1,
                    query="What is machine learning?",
                    mode=KnowledgeMode.AUTO,
                )
        assert result["case"] in (KnowledgeCase.FULL_DOCUMENT, KnowledgeCase.MULTI_DOCUMENT, KnowledgeCase.PARTIAL_DOCUMENT)
        assert result["confidence"] in ("high", "medium", "low", "none")
        assert len(result["chunks"]) >= 1

    @pytest.mark.asyncio
    async def test_hybrid_engine_no_documents(self, db_session_mock):
        engine = HybridKnowledgeEngine(db=db_session_mock)
        with patch.object(engine, "_hybrid_retrieve", new=AsyncMock(return_value=[])):
            with patch.object(engine, "_get_memory_context", new=AsyncMock(return_value=[])):
                result = await engine.retrieve_and_decide(user_id=1, query="obscure topic xyz")
        assert result["case"] == KnowledgeCase.NO_DOCUMENT

    @pytest.mark.asyncio
    async def test_hybrid_engine_enrich_citations(self, db_session_mock):
        from app.models.document import Document

        doc = Document(id=1, filename="ml_guide.pdf", user_id=1)
        db_session_mock.exec.return_value.first.return_value = doc
        engine = HybridKnowledgeEngine(db=db_session_mock)
        enriched = engine.enrich_citations(MOCK_CHUNKS)
        assert enriched[0].get("document_name") == "ml_guide.pdf"
        assert "snippet" in enriched[0]

    def test_rag_evaluation_metrics_benchmark(self):
        """Benchmark retrieval quality metrics on a fixed relevance set."""
        relevant_ranks = [1, 2, 4]
        mrr = compute_mrr(relevant_ranks)
        assert mrr > 0.5

        precision = compute_precision_at_k(3, 5)
        assert precision == 0.6

        ndcg = compute_ndcg_at_k([3.0, 2.0, 1.0, 0.0], k=4)
        assert 0.0 < ndcg <= 1.0


@pytest.mark.asyncio
async def test_query_vectors_with_mock():
    with patch("app.rag.retriever.vector_store") as mock_store:
        mock_store.query.return_value = {
            "documents": [["test doc"]],
            "metadatas": [[{"document_id": 1}]],
            "distances": [[0.1]],
        }
        result = query_vectors(embedding=[0.1] * 8, k=1, where={"user_id": 1})
        assert "documents" in result
