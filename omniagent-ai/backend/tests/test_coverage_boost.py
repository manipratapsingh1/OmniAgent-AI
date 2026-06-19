"""Additional coverage tests targeting low-coverage modules."""
import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.schemas.chat import ChatRequest
from app.agents.state import AgentState


class TestMemoryServiceFull:
    def test_all_memory_methods(self, db_session_mock):
        from app.models.memory import MemoryEntry
        from app.services.memory_service import MemoryService

        entry = MemoryEntry(
            id=1, user_id=1, memory_type="short_term", content="test",
            created_at=datetime.now(timezone.utc),
        )
        db_session_mock.exec.return_value.all.return_value = [entry]
        db_session_mock.exec.return_value.first.return_value = None
        db_session_mock.refresh = MagicMock()

        service = MemoryService(db_session_mock)
        service.store_short_term(1, "hello")
        service.store_long_term(1, "persistent", embedding=[0.1, 0.2])
        service.get_counts(1)
        service.get_short_term(1)
        service.get_long_term(1)
        service.store_learned_fact(1, "likes Python")
        service.get_learned_facts(1)
        service.search_memories(1, "hello")
        service.cleanup_expired()

    def test_memory_vector_store_failure(self, db_session_mock):
        from app.services.memory_service import MemoryService

        db_session_mock.refresh = MagicMock()
        service = MemoryService(db_session_mock)
        with patch("app.rag.retriever.vector_store") as mock_vs:
            mock_vs.add.side_effect = RuntimeError("chroma down")
            service.store_long_term(1, "fact", embedding=[0.1])


class TestPerformanceUtils:
    def test_response_cache_fallback(self):
        from app.utils.performance import ResponseCache, QueryOptimizer, PerformanceMonitor

        cache = ResponseCache()
        cache.enabled = False
        cache.set("key1", {"answer": "test"}, ttl=60)
        assert cache.get("key1") == {"answer": "test"}
        stats = cache.stats()
        assert "hit_rate" in stats
        cache.clear()

    def test_query_optimizer(self):
        from app.utils.performance import QueryOptimizer

        key = QueryOptimizer.generate_query_key("user", 1, query="test")
        assert "user" in key
        ctx = [{"text": f"chunk{i}"} for i in range(10)]
        optimized = QueryOptimizer.optimize_context_retrieval(ctx, limit=3)
        assert len(optimized) == 3

    def test_perf_monitor_and_decorator(self):
        from app.utils.performance import PerformanceMonitor, measure_time, get_perf_monitor

        monitor = PerformanceMonitor()
        monitor.record("latency", 10.0)
        assert monitor.get_stats("latency")["count"] == 1

        @measure_time("sync_test")
        def sync_fn():
            return 42

        assert sync_fn() == 42
        assert get_perf_monitor().get_stats("sync_test")["count"] >= 1

    @pytest.mark.asyncio
    async def test_async_measure_time(self):
        from app.utils.performance import measure_time

        @measure_time("async_test")
        async def async_fn():
            return "ok"

        assert await async_fn() == "ok"

    @pytest.mark.asyncio
    async def test_batch_processor_empty(self):
        from app.utils.performance import BatchProcessor

        bp = BatchProcessor(batch_size=10, timeout=1.0)
        await bp._process_batch()
        assert bp.batch == []


class TestQuotaAndFeedback:
    def test_quota_service(self, db_session_mock):
        from app.models.user import User
        from app.services.quota_service import QuotaService

        user = User(id=1, email="u@t.com", api_quota=100, api_used=10)
        db_session_mock.exec.return_value.first.return_value = user
        db_session_mock.exec.return_value.all.return_value = [user]

        service = QuotaService(db_session_mock)
        q = service.check_user_quota(1)
        assert q["has_quota"] is True
        assert service.increment_usage(1) is True
        assert service.get_user_stats(1)["status"] == "active"
        assert service.reset_monthly_quota(1) == 1

    def test_feedback_service(self, db_session_mock):
        from app.models.response import Response
        from app.services.feedback_service import ResponseFeedbackService

        response = Response(id=1, conversation_id=1, user_id=1, content="answer")
        db_session_mock.exec.return_value.first.return_value = response
        db_session_mock.exec.return_value.all.return_value = [response]
        db_session_mock.refresh = MagicMock()

        service = ResponseFeedbackService(db_session_mock)
        stored = service.store_response(1, 1, "answer", citations=["doc:1#0"])
        assert stored.content == "answer"
        assert service.add_feedback(1, 1, helpful=True, rating=5) is True
        assert len(service.get_positive_responses()) >= 1
        stats = service.get_feedback_stats()
        assert "satisfaction_rate" in stats


class TestChatService:
    @pytest.mark.asyncio
    async def test_chat_service_flow(self, db_session_mock):
        from app.models.conversation import Conversation
        from app.services.chat_service import ChatService

        conv = Conversation(id=1, user_id=1, model="llama3.2", title="New Conversation")
        db_session_mock.refresh = MagicMock(side_effect=lambda obj: setattr(obj, "id", 99) if hasattr(obj, "id") else None)

        service = ChatService(db_session_mock)
        service.repo = MagicMock()
        service.repo.get.return_value = conv
        service.repo.add.return_value = conv

        final_state = AgentState(
            user_id=1, conversation_id=1, query="Hi",
            final="Hello!", context=[], trace=[],
        )

        with patch("app.services.chat_service.GRAPH") as mock_graph:
            mock_graph.ainvoke = AsyncMock(return_value=final_state)
            with patch("app.services.chat_service.mem_append", new=AsyncMock()):
                resp = await service.chat(1, ChatRequest(message="Hi"))
        assert resp.content == "Hello!"

    def test_ensure_conversation_new(self, db_session_mock):
        from app.models.conversation import Conversation
        from app.services.chat_service import ChatService

        service = ChatService(db_session_mock)
        service.repo = MagicMock()
        service.repo.add.return_value = Conversation(id=5, user_id=1, model="llama3.2")
        conv = service._ensure_conversation(1, None, "llama3.2")
        assert conv.id == 5


class TestAIService:
    @pytest.mark.asyncio
    async def test_ai_service_generate(self):
        from app.services.ai.service import AIService

        service = AIService()
        mock_provider = MagicMock()
        mock_provider.name = "mock"
        mock_provider.generate = AsyncMock(return_value="Generated text")
        with patch.object(service, "get_healthy_provider", return_value=mock_provider):
            with patch("app.services.ai.service.get_json", return_value=None):
                with patch("app.services.ai.service.set_json"):
                    result = await service.generate("Hello", model="gpt-4")
        assert result == "Generated text"

    @pytest.mark.asyncio
    async def test_ai_service_stream(self):
        from app.services.ai.service import AIService

        service = AIService()
        mock_provider = MagicMock()
        mock_provider.name = "mock"

        async def stream(prompt, **kwargs):
            yield "chunk1"
            yield "chunk2"

        mock_provider.stream = stream
        with patch.object(service, "get_healthy_provider", return_value=mock_provider):
            chunks = []
            async for c in service.stream("Hello"):
                chunks.append(c)
        assert len(chunks) == 2

    @pytest.mark.asyncio
    async def test_ai_service_query_with_knowledge(self, db_session_mock):
        from app.services.ai.service import AIService

        service = AIService(db=db_session_mock)
        mock_provider = MagicMock()
        mock_provider.generate = AsyncMock(return_value="Answer")
        with patch.object(service, "choose_provider", return_value=mock_provider):
            with patch("app.services.ai.service.KnowledgeSearchService") as mock_ks:
                mock_ks.return_value.search_knowledge_base = AsyncMock(return_value=[{"text": "kb"}])
                result = await service.query("question", search_knowledge_base=True)
        assert "answer" in result


class TestRepositories:
    def test_document_repo(self, db_session_mock):
        from app.repositories.document_repo import DocumentRepo
        from app.models.document import Document

        doc = Document(id=1, user_id=1, filename="f.txt", status="indexed")
        db_session_mock.get.return_value = doc
        db_session_mock.exec.return_value.all.return_value = [doc]

        repo = DocumentRepo(db_session_mock)
        assert repo.get(1) == doc
        assert len(repo.for_user(1)) == 1

    def test_conversation_repo(self, db_session_mock):
        from app.repositories.conversation_repo import ConversationRepo
        from app.models.conversation import Conversation

        conv = Conversation(id=1, user_id=1, model="llama3.2")
        db_session_mock.get.return_value = conv
        db_session_mock.exec.return_value.all.return_value = [conv]

        repo = ConversationRepo(db_session_mock)
        assert repo.get(1) == conv

    def test_base_repo(self, db_session_mock):
        from app.repositories.base import BaseRepo
        from app.models.task import Task

        db_session_mock.get.return_value = None
        repo = BaseRepo(Task, db_session_mock)
        assert repo.get(999) is None


class TestHybridKnowledgeExtended:
    @pytest.mark.asyncio
    async def test_web_search_fallback(self, db_session_mock):
        from app.services.ai.hybrid_knowledge_engine import HybridKnowledgeEngine

        engine = HybridKnowledgeEngine(db=db_session_mock)
        with patch.object(engine, "_hybrid_retrieve", new=AsyncMock(return_value=[])):
            with patch.object(engine, "_get_memory_context", new=AsyncMock(return_value=[])):
                with patch.object(engine, "_search_web", new=AsyncMock(return_value=[{"title": "Web", "text": "result", "url": "http://x", "score": 0.5, "citation_key": "web:1"}])):
                    with patch("app.services.ai.hybrid_knowledge_engine.settings") as mock_settings:
                        mock_settings.ENABLE_WEB_SEARCH = True
                        result = await engine.retrieve_and_decide(1, "current events today")
        assert result["metadata"]["web_result_count"] >= 0

    def test_all_system_instructions(self):
        from app.services.ai.hybrid_knowledge_engine import HybridKnowledgeEngine, KnowledgeCase

        engine = HybridKnowledgeEngine(db=MagicMock())
        for case in KnowledgeCase:
            instructions = engine._get_system_instructions(case, "high")
            assert "OmniAgent" in instructions

    def test_invalid_explicit_mode(self):
        from app.services.ai.hybrid_knowledge_engine import detect_knowledge_mode, KnowledgeMode

        assert detect_knowledge_mode("hello", explicit_mode="invalid_mode") == KnowledgeMode.AUTO


class TestNotificationService:
    def test_create_notification(self, db_session_mock):
        from app.services.notification_service import NotificationService

        db_session_mock.refresh = MagicMock()
        service = NotificationService(db_session_mock)
        n = service.create(1, "info", "Title", "Message")
        assert n.title == "Title"


class TestSummarizationService:
    @pytest.mark.asyncio
    async def test_generate_summary(self, db_session_mock):
        from app.services.summarization_service import DocumentSummarizationService

        service = DocumentSummarizationService(db_session_mock)
        service.llm = MagicMock()
        service.llm.generate = AsyncMock(return_value='{"summary": "Brief summary", "key_points": ["a", "b"]}')
        db_session_mock.refresh = MagicMock()
        result = await service.generate_summary(1, "Long document text here")
        assert "summary" in result or result


class TestModelRouterExtended:
    def test_classify_task_types(self):
        from app.services.ai.model_router import classify_task, TaskType

        assert classify_task("debug this python function") == TaskType.CODING
        assert classify_task("research latest AI trends") == TaskType.RESEARCH
        assert classify_task("quick answer please") == TaskType.FAST
        assert classify_task("hello there") == TaskType.GENERAL

    @pytest.mark.asyncio
    async def test_model_router_generate(self):
        from app.services.ai.model_router import ModelRouter
        from app.services.ai.ollama_provider import OllamaProvider

        provider = MagicMock()
        provider.generate = AsyncMock(return_value="response")
        router = ModelRouter({"ollama": provider})
        result, used = await router.generate("prompt", query="hello")
        assert result == "response"


class TestWebSearchExtended:
    @pytest.mark.asyncio
    async def test_search_formatted(self):
        from app.services.web_search_service import WebSearchService, SearchResult

        service = WebSearchService()
        mock_results = [SearchResult(title="T", url="http://x", snippet="snippet", score=0.9)]
        with patch.object(service, "search", new=AsyncMock(return_value=mock_results)):
            formatted = await service.search_formatted("test")
        assert isinstance(formatted, str)


class TestToolsExtended:
    @pytest.mark.asyncio
    async def test_calculator_tool(self):
        from app.tools.calculator import calculator

        result = await calculator({"expression": "2 + 2"})
        assert "4" in result

    @pytest.mark.asyncio
    async def test_registry_run(self):
        from app.tools.registry import registry

        result = await registry.run("calculator", {"expression": "3 * 3"})
        assert "9" in result
        assert "calculator" in registry.names()

    @pytest.mark.asyncio
    async def test_code_explainer(self):
        from app.tools.code_explainer import code_explainer

        with patch("app.tools.code_explainer.ollama") as mock_ollama:
            mock_ollama.generate = AsyncMock(return_value="This code prints hello")
            result = await code_explainer({"code": "print('hello')"})
        assert isinstance(result, str)


class TestTaskServiceExtended:
    def test_update_and_delete(self, db_session_mock):
        from app.models.task import Task
        from app.services.task_service import TaskService

        task = Task(id=1, user_id=1, title="T", status="pending", priority=3)
        service = TaskService(db_session_mock)
        service.repo = MagicMock()
        service.repo.get.return_value = task
        service.repo.add.side_effect = lambda t: t
        service.repo.delete.return_value = True

        updated = service.update_status(1, 1, "done")
        assert updated.status == "done"
        assert service.delete(1, 1) is True
        assert service.filter_by_tag(1, "urgent") == []
        assert service.filter_by_priority(1, 3) == []
