"""Coverage for remaining service modules."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestSharingFaqService:
    @pytest.mark.asyncio
    async def test_create_share(self, db_session_mock):
        from app.services.sharing_faq_service import SharingAndFAQService

        service = SharingAndFAQService(db_session_mock)
        db_session_mock.refresh = MagicMock()
        result = await service.create_share(1, 1, expires_in_hours=24)
        assert "share_token" in result

    @pytest.mark.asyncio
    async def test_create_template(self, db_session_mock):
        from app.services.sharing_faq_service import SharingAndFAQService

        service = SharingAndFAQService(db_session_mock)
        db_session_mock.refresh = MagicMock()
        template = await service.create_query_template("Tax FAQ", "How do I file?", "legal")
        assert template["title"] == "Tax FAQ"


class TestTaggingService:
    @pytest.mark.asyncio
    async def test_add_tags(self, db_session_mock):
        from app.services.tagging_service import TaggingService

        service = TaggingService(db_session_mock)
        result = await service.add_tags(1, ["finance", "tax"], category="legal")
        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_get_document_tags(self, db_session_mock):
        from app.models.document_tags import DocumentTag
        from app.services.tagging_service import TaggingService

        tag = DocumentTag(document_id=1, tag="finance")
        db_session_mock.exec.return_value.all.return_value = [tag]
        service = TaggingService(db_session_mock)
        tags = await service.get_document_tags(1)
        assert "finance" in tags

    @pytest.mark.asyncio
    async def test_create_category(self, db_session_mock):
        from app.services.tagging_service import TaggingService

        service = TaggingService(db_session_mock)
        db_session_mock.refresh = MagicMock()
        result = await service.create_category("Finance", description="Finance docs", color="#blue")
        assert result["name"] == "Finance"


class TestNotificationServiceExtended:
    def test_mark_as_read(self, db_session_mock):
        from app.models.notification import Notification
        from app.services.notification_service import NotificationService

        notif = Notification(id=1, user_id=1, notification_type="info", title="T", message="M", is_read=False)
        db_session_mock.exec.return_value.first.return_value = notif
        db_session_mock.exec.return_value.all.return_value = [notif]
        service = NotificationService(db_session_mock)
        assert service.mark_as_read(1, 1) is True
        service.mark_all_read(1)


class TestFeedbackServiceExtended:
    def test_get_stats_empty(self, db_session_mock):
        from app.services.feedback_service import ResponseFeedbackService

        db_session_mock.exec.return_value.all.return_value = []
        service = ResponseFeedbackService(db_session_mock)
        stats = service.get_feedback_stats()
        assert stats["total_feedback"] == 0


class TestOptimizedRetriever:
    @pytest.mark.asyncio
    async def test_optimized_retrieve(self):
        from app.rag.optimized_retriever import OptimizedRAGRetriever

        mock_collection = MagicMock()
        mock_collection.query.return_value = {
            "documents": [["text"]],
            "metadatas": [[{"document_id": 1, "chunk_index": 0}]],
            "distances": [[0.1]],
        }
        retriever = OptimizedRAGRetriever(mock_collection)
        with patch("app.rag.embeddings.embed_texts", new=AsyncMock(return_value=[[0.1] * 4])):
            results = await retriever.retrieve("test query", limit=3)
        assert isinstance(results, list)


class TestHybridEngineHybridRetrieve:
    @pytest.mark.asyncio
    async def test_hybrid_retrieve_path(self, db_session_mock):
        from app.services.ai.hybrid_knowledge_engine import HybridKnowledgeEngine

        engine = HybridKnowledgeEngine(db=db_session_mock)
        mock_chunks = [{"document_id": 1, "chunk_index": 0, "text": "ml content", "score": 0.8}]
        with patch("app.services.ai.hybrid_knowledge_engine.retrieve", new=AsyncMock(return_value=mock_chunks)):
            with patch("app.services.ai.hybrid_knowledge_engine._keyword_search_fallback", return_value=mock_chunks):
                results = await engine._hybrid_retrieve(1, "machine learning", k=3)
        assert len(results) >= 1


class TestAIServiceExtended:
    @pytest.mark.asyncio
    async def test_embed(self):
        from app.services.ai.service import AIService

        service = AIService()
        mock_provider = MagicMock()
        mock_provider.embed = AsyncMock(return_value=[[0.1, 0.2]])
        with patch.object(service, "choose_provider", return_value=mock_provider):
            result = await service.embed(["hello"])
        assert len(result) == 1

    def test_choose_provider_fallback(self):
        from app.services.ai.service import AIService

        service = AIService()
        provider = service.choose_provider("nonexistent")
        assert provider is not None


class TestMemoryLongTerm:
    def test_store_learned_fact_update(self, db_session_mock):
        from app.models.memory import LearnedFact
        from app.services.memory_service import MemoryService

        existing = LearnedFact(id=1, user_id=1, fact="likes coffee", category="preference")
        db_session_mock.exec.return_value.first.return_value = existing
        service = MemoryService(db_session_mock)
        service.store_learned_fact(1, "likes coffee")
        db_session_mock.commit.assert_called()


class TestSchemasCommonExtended:
    def test_search_params(self):
        from app.schemas.common import SearchParams, TimeRangeParams, StatusResponse

        s = SearchParams(query="hello world")
        assert s.query == "hello world"
        t = TimeRangeParams()
        assert t.start_date is None
        status = StatusResponse(status="ok")
        assert status.status == "ok"

    def test_sort_params_invalid(self):
        from app.schemas.common import SortParams

        with pytest.raises(ValueError):
            SortParams(sort_order="invalid")

    def test_search_query_too_short(self):
        from app.schemas.common import SearchParams

        with pytest.raises(ValueError):
            SearchParams(query="a")
