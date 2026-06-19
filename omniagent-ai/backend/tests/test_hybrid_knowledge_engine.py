"""Tests for Hybrid Knowledge Engine and hybrid search."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.rag.hybrid_search import (
    bm25_score,
    reciprocal_rank_fusion,
    hybrid_merge,
    filter_irrelevant_chunks,
    assess_retrieval_confidence,
)
from app.services.ai.hybrid_knowledge_engine import (
    HybridKnowledgeEngine,
    KnowledgeMode,
    KnowledgeCase,
    detect_knowledge_mode,
)


class TestHybridSearch:
    def test_bm25_score_exact_match(self):
        score = bm25_score("machine learning", "machine learning is a subset of AI")
        assert score > 0

    def test_bm25_score_no_match(self):
        score = bm25_score("quantum physics", "the weather is sunny today")
        assert score == 0.0

    def test_reciprocal_rank_fusion(self):
        list_a = [
            {"document_id": 1, "chunk_index": 0, "chunk_key": "1:0", "score": 0.9},
            {"document_id": 2, "chunk_index": 1, "chunk_key": "2:1", "score": 0.7},
        ]
        list_b = [
            {"document_id": 2, "chunk_index": 1, "chunk_key": "2:1", "score": 0.8},
            {"document_id": 3, "chunk_index": 0, "chunk_key": "3:0", "score": 0.6},
        ]
        fused = reciprocal_rank_fusion([list_a, list_b])
        assert len(fused) == 3
        assert fused[0]["chunk_key"] in ("1:0", "2:1")

    def test_hybrid_merge(self):
        vector = [
            {"document_id": 1, "chunk_index": 0, "text": "machine learning algorithms", "score": 0.85},
        ]
        keyword = [
            {"document_id": 2, "chunk_index": 0, "text": "deep learning neural networks", "score": 0.1},
        ]
        merged = hybrid_merge(vector, keyword, "machine learning", top_k=5)
        assert len(merged) >= 1
        assert merged[0]["document_id"] == 1

    def test_filter_irrelevant(self):
        chunks = [
            {"text": "highly relevant machine learning content", "score": 0.8},
            {"text": "xyz abc random noise", "score": 0.001},
        ]
        filtered = filter_irrelevant_chunks(chunks, "machine learning", min_score=0.05)
        assert len(filtered) >= 1

    def test_assess_confidence(self):
        assert assess_retrieval_confidence([]) == "none"
        assert assess_retrieval_confidence([{"score": 0.8}]) == "high"
        assert assess_retrieval_confidence([{"score": 0.4}]) == "medium"
        assert assess_retrieval_confidence([{"score": 0.15}]) == "low"


class TestKnowledgeModeDetection:
    def test_auto_mode_default(self):
        assert detect_knowledge_mode("What is Python?") == KnowledgeMode.AUTO

    def test_documents_only_detection(self):
        assert detect_knowledge_mode("Answer only from my documents about taxes") == KnowledgeMode.DOCUMENTS_ONLY
        assert detect_knowledge_mode("Use only documents please") == KnowledgeMode.DOCUMENTS_ONLY

    def test_ai_only_detection(self):
        assert detect_knowledge_mode("Use your own knowledge to explain quantum physics") == KnowledgeMode.AI_ONLY
        assert detect_knowledge_mode("Don't use my documents, just tell me") == KnowledgeMode.AI_ONLY

    def test_explicit_mode_override(self):
        assert detect_knowledge_mode("anything", explicit_mode="documents_only") == KnowledgeMode.DOCUMENTS_ONLY


class TestHybridKnowledgeEngine:
    def test_determine_case_no_document(self):
        engine = HybridKnowledgeEngine(db=MagicMock())
        case = engine._determine_case(KnowledgeMode.AUTO, [], "none")
        assert case == KnowledgeCase.NO_DOCUMENT

    def test_determine_case_multi_document(self):
        engine = HybridKnowledgeEngine(db=MagicMock())
        chunks = [
            {"document_id": 1, "score": 0.8},
            {"document_id": 2, "score": 0.7},
        ]
        case = engine._determine_case(KnowledgeMode.AUTO, chunks, "high")
        assert case == KnowledgeCase.MULTI_DOCUMENT

    def test_determine_case_full_document(self):
        engine = HybridKnowledgeEngine(db=MagicMock())
        chunks = [{"document_id": 1, "score": 0.8}]
        case = engine._determine_case(KnowledgeMode.AUTO, chunks, "high")
        assert case == KnowledgeCase.FULL_DOCUMENT

    def test_determine_case_documents_only_mode(self):
        engine = HybridKnowledgeEngine(db=MagicMock())
        case = engine._determine_case(KnowledgeMode.DOCUMENTS_ONLY, [], "none")
        assert case == KnowledgeCase.DOCUMENTS_ONLY

    def test_build_prompt_ai_only(self):
        engine = HybridKnowledgeEngine(db=MagicMock())
        result = {
            "case": KnowledgeCase.AI_ONLY,
            "context_text": "",
            "system_instructions": "AI only mode",
            "chunks": [],
        }
        prompt, system = engine.build_prompt("What is AI?", result)
        assert "What is AI?" in prompt
        assert system == "AI only mode"

    def test_build_prompt_documents_only_no_chunks(self):
        engine = HybridKnowledgeEngine(db=MagicMock())
        result = {
            "case": KnowledgeCase.DOCUMENTS_ONLY,
            "context_text": "",
            "system_instructions": "Docs only",
            "chunks": [],
        }
        prompt, _ = engine.build_prompt("Find taxes info", result)
        assert "Information not found" in prompt or "No relevant documents" in prompt

    def test_format_context_with_metadata(self):
        engine = HybridKnowledgeEngine(db=MagicMock())
        chunks = [
            {
                "document_id": 1,
                "chunk_index": 0,
                "text": "Sample content",
                "page_number": 3,
                "section": "Introduction",
                "score": 0.85,
            }
        ]
        context = engine._format_context(chunks, [])
        assert "page:3" in context
        assert "section:Introduction" in context
        assert "Sample content" in context

    @pytest.mark.asyncio
    async def test_retrieve_and_decide_ai_only(self):
        db = MagicMock()
        engine = HybridKnowledgeEngine(db=db)
        result = await engine.retrieve_and_decide(
            user_id=1,
            query="Use your own knowledge about Python",
            mode=KnowledgeMode.AI_ONLY,
        )
        assert result["case"] == KnowledgeCase.AI_ONLY
        assert result["chunks"] == []
        assert result["confidence"] == "none"
