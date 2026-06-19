"""Failure recovery tests — simulate external service outages and degraded modes."""
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.utils.resilience import CircuitBreaker, CircuitState, breakers
from app.utils.health_check import HealthChecker
from app.rag.ingest import ingest_file
from app.rag.retriever import VectorStore
from app.services.ai.service import AIService
from app.services.web_search_service import WebSearchService


class TestDatabaseDown:
    def test_diagnose_reports_failure(self):
        with patch("app.db.session.engine") as mock_engine:
            mock_engine.connect.side_effect = Exception("connection refused")
            from app.utils.db_diagnostics import diagnose_database_connection
            result = diagnose_database_connection()
            assert result["connection_successful"] is False
            assert result["error"] is not None


class TestRedisDown:
    @pytest.mark.asyncio
    async def test_health_check_redis_failure(self):
        redis = MagicMock()
        redis.ping.side_effect = ConnectionError("Redis connection refused")
        checker = HealthChecker(MagicMock(), redis, "http://ollama:11434", "http://chroma:8000")
        result = await checker._check_redis()
        assert result["status"] == "unhealthy"
        assert "error" in result

    @pytest.mark.asyncio
    async def test_circuit_breaker_redis_opens(self):
        cb = breakers["redis"]
        original_state = cb.state
        original_count = cb.failure_count
        try:
            cb.failure_count = cb.failure_threshold
            cb.state = CircuitState.OPEN
            cb.last_failure_time = time.time()

            async def redis_op():
                return True

            with pytest.raises(Exception, match="OPEN"):
                await cb.call(redis_op)
        finally:
            cb.state = original_state
            cb.failure_count = original_count


class TestChromaDown:
    @pytest.mark.asyncio
    async def test_ingest_fails_when_chroma_unavailable(self):
        with patch("app.rag.ingest._extract_text", return_value="Test content " * 20):
            with patch("app.rag.ingest.semantic_chunk_text", return_value=["chunk1"]):
                with patch("app.rag.ingest.embed_texts", new=AsyncMock(return_value=[[0.1] * 4])):
                    with patch("app.rag.ingest.vector_store") as mock_store:
                        mock_store.add.side_effect = RuntimeError("Chroma connection refused")
                        n_chunks, _, ids, _ = await ingest_file(1, 1, "test.txt", b"x")
        assert n_chunks == 0

    @pytest.mark.asyncio
    async def test_health_check_chroma_failure(self):
        checker = HealthChecker(MagicMock(), MagicMock(), "http://ollama:11434", "http://chroma:8000")
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                side_effect=ConnectionError("Chroma unreachable")
            )
            result = await checker._check_chroma()
        assert result["status"] == "unhealthy"


class TestOllamaDown:
    @pytest.mark.asyncio
    async def test_embedding_failure_on_ollama_down(self):
        with patch("app.rag.ingest._extract_text", return_value="Content " * 30):
            with patch("app.rag.ingest.semantic_chunk_text", return_value=["c1", "c2"]):
                with patch(
                    "app.rag.ingest.embed_texts",
                    new=AsyncMock(side_effect=TimeoutError("Ollama embedding timeout")),
                ):
                    n_chunks, _, ids, _ = await ingest_file(1, 1, "test.txt", b"x")
        assert n_chunks == 0
        assert ids == []

    @pytest.mark.asyncio
    async def test_health_check_ollama_timeout(self):
        checker = HealthChecker(MagicMock(), MagicMock(), "http://ollama:11434", "http://chroma:8000")
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                side_effect=TimeoutError("API timeout")
            )
            result = await checker._check_ollama()
        assert result["status"] == "unhealthy"


class TestAPITimeout:
    @pytest.mark.asyncio
    async def test_web_search_timeout_graceful(self):
        service = WebSearchService()
        with patch.object(service, "_search_duckduckgo", new=AsyncMock(side_effect=TimeoutError("timeout"))):
            results = await service.search("test query")
        assert isinstance(results, list)


class TestEmbeddingFailure:
    @pytest.mark.asyncio
    async def test_batch_embedding_exception_returns_zero(self):
        with patch("app.rag.ingest._extract_text", return_value="Text " * 100):
            with patch("app.rag.ingest.semantic_chunk_text", return_value=["a"] * 35):
                with patch("app.rag.ingest.embed_texts", new=AsyncMock(side_effect=RuntimeError("embedding model error"))):
                    n_chunks, n_vectors, ids, chunks = await ingest_file(1, 1, "large.txt", b"x")
        assert n_chunks == 0
        assert n_vectors == 0


class TestCorruptFileUpload:
    def test_corrupt_pdf_returns_empty(self):
        from app.rag.ingest import _extract_text
        text = _extract_text("corrupt.pdf", b"NOT_A_VALID_PDF")
        assert text == ""

    def test_corrupt_binary_no_crash(self):
        from app.rag.ingest import _extract_text
        text = _extract_text("binary.bin", bytes(range(256)))
        assert isinstance(text, str)

    @pytest.mark.asyncio
    async def test_upload_empty_file_fails_gracefully(self):
        from app.services.document_service import DocumentService

        db = MagicMock()
        with patch.object(DocumentService, "__init__", lambda self, db: None):
            service = DocumentService(db)
            service.db = db
            service.repo = MagicMock()
            service.repo.add.side_effect = lambda d: d

            with patch("app.services.document_service.ingest_file", new=AsyncMock(return_value=(0, 0, [], []))):
                with patch("app.services.document_service.AuditService"):
                    doc = await service.upload(1, "empty.txt", "text/plain", b"")
        assert doc.status == "failed"


class TestCircuitBreakerRecovery:
    @pytest.mark.asyncio
    async def test_half_open_recovery(self):
        cb = CircuitBreaker("recovery_test", failure_threshold=2, recovery_timeout=0)

        async def succeed():
            return "recovered"

        cb.failure_count = 2
        cb.state = CircuitState.OPEN
        cb.last_failure_time = time.time() - 1

        result = await cb.call(succeed)
        assert result == "recovered"
        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 0
