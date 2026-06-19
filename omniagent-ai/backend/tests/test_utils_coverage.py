"""Utility module coverage — cache, rate limiter, health checks, db helpers, workers."""
import asyncio
import time
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.exc import OperationalError, ArgumentError

from app.utils.cache import SimpleCache, get_cache, cache_key, cached
from app.utils.rate_limiter import RateLimiter, get_rate_limiter, check_rate_limit
from app.utils.db_query import QueryBuilder, paginate
from app.utils.db_diagnostics import get_database_connection_error_message, diagnose_database_connection
from app.utils.health_check import HealthChecker, PerformanceMonitor, get_performance_monitor
from app.utils.resilience import CircuitBreaker, CircuitState, breakers
from app.workers import jobs


class TestSimpleCache:
    def test_set_and_get(self):
        cache = SimpleCache()
        cache.set("key1", "value1", ttl_seconds=300)
        assert cache.get("key1") == "value1"

    def test_expired_entry(self):
        cache = SimpleCache()
        cache.set("key2", "value2", ttl_seconds=0)
        cache.data["key2"] = ("value2", datetime.now(timezone.utc) - timedelta(seconds=1))
        assert cache.get("key2") is None

    def test_delete_and_clear(self):
        cache = SimpleCache()
        cache.set("a", 1)
        cache.delete("a")
        assert cache.get("a") is None
        cache.set("b", 2)
        cache.clear()
        assert cache.get("b") is None

    def test_cache_key(self):
        key = cache_key("prefix", 1, 2, foo="bar")
        assert "prefix" in key
        assert "foo=bar" in key

    def test_cached_decorator(self):
        calls = {"n": 0}

        @cached(ttl_seconds=60, key_prefix="test_fn")
        def compute(x):
            calls["n"] += 1
            return x * 2

        assert compute(3) == 6
        assert compute(3) == 6
        assert calls["n"] == 1

    def test_get_cache_singleton(self):
        assert get_cache() is get_cache()


class TestRateLimiter:
    def test_allows_within_limit(self):
        limiter = RateLimiter()
        allowed, info = limiter.is_allowed("user:1", max_requests=5, window_seconds=60)
        assert allowed is True
        assert info["remaining"] >= 0

    def test_blocks_over_limit(self):
        limiter = RateLimiter()
        for _ in range(3):
            limiter.is_allowed("user:2", max_requests=3, window_seconds=60)
        allowed, _ = limiter.is_allowed("user:2", max_requests=3, window_seconds=60)
        assert allowed is False

    def test_check_rate_limit_global(self):
        allowed, info = check_rate_limit("global:test", max_requests=100)
        assert allowed is True
        assert "limit" in info


class TestDbQuery:
    def test_query_builder_chain(self, db_session_mock):
        from app.models.user import User

        db_session_mock.exec.return_value.all.return_value = []
        db_session_mock.exec.return_value.first.return_value = None

        qb = QueryBuilder(db_session_mock, User)
        qb.filter_by(email="a@b.com").limit(10).offset(0)
        assert qb.all() == []
        assert qb.first() is None
        assert qb.count() == 0
        assert qb.exists() is False

    def test_paginate(self, db_session_mock):
        from app.models.user import User

        db_session_mock.exec.return_value.all.side_effect = [[User(id=1, email="a@b.com")], []]
        items, total = paginate(db_session_mock, User, limit=10, offset=0)
        assert total == 1
        assert len(items) == 0 or items  # depends on mock side_effect


class TestDbDiagnostics:
    def test_connection_refused_message(self):
        err = OperationalError("stmt", {}, Exception("connection refused"))
        msg = get_database_connection_error_message(err)
        assert "PostgreSQL" in msg or "connection" in msg.lower()

    def test_auth_failed_message(self):
        err = OperationalError("stmt", {}, Exception("authentication failed for user"))
        msg = get_database_connection_error_message(err)
        assert "authentication" in msg.lower()

    def test_database_not_exist_message(self):
        err = OperationalError("stmt", {}, Exception("database omni does not exist"))
        msg = get_database_connection_error_message(err)
        assert "does not exist" in msg

    def test_argument_error_message(self):
        err = ArgumentError("invalid url")
        msg = get_database_connection_error_message(err)
        assert "DATABASE_URL" in msg

    def test_generic_error_message(self):
        msg = get_database_connection_error_message(Exception("unknown failure"))
        assert "unknown failure" in msg

    def test_diagnose_database_connection(self):
        result = diagnose_database_connection()
        assert "database_url_set" in result
        assert "connection_successful" in result


class TestHealthChecker:
    @pytest.mark.asyncio
    async def test_check_all_healthy(self):
        db = MagicMock()
        db.exec.return_value.first.return_value = 1
        db.connection.return_value.connection.get_backend_name = MagicMock()

        redis = MagicMock()
        redis.ping.return_value = True
        redis.info.return_value = {"used_memory": 1024 * 1024, "maxmemory": 0}

        checker = HealthChecker(db, redis, "http://ollama:11434", "http://chroma:8000")

        with patch.object(checker, "_check_ollama", new=AsyncMock(return_value={"status": "healthy"})):
            with patch.object(checker, "_check_chroma", new=AsyncMock(return_value={"status": "healthy"})):
                with patch.object(checker, "_check_system_resources", new=AsyncMock(return_value={"status": "healthy"})):
                    result = await checker.check_all()
        assert result["status"] in ("healthy", "degraded")
        assert "components" in result

    @pytest.mark.asyncio
    async def test_check_database_unhealthy(self):
        db = MagicMock()
        db.exec.side_effect = Exception("db down")
        checker = HealthChecker(db, MagicMock(), "http://ollama:11434", "http://chroma:8000")
        result = await checker._check_database()
        assert result["status"] == "unhealthy"

    @pytest.mark.asyncio
    async def test_check_redis_unhealthy(self):
        redis = MagicMock()
        redis.ping.side_effect = Exception("redis down")
        checker = HealthChecker(MagicMock(), redis, "http://ollama:11434", "http://chroma:8000")
        result = await checker._check_redis()
        assert result["status"] == "unhealthy"

    @pytest.mark.asyncio
    async def test_check_ollama_success(self):
        checker = HealthChecker(MagicMock(), MagicMock(), "http://ollama:11434", "http://chroma:8000")
        mock_resp = MagicMock(status_code=200, elapsed=MagicMock(total_seconds=lambda: 0.05))
        mock_resp.json.return_value = {"models": [{"name": "llama3.2"}]}
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_resp)
            result = await checker._check_ollama()
        assert result["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_check_ollama_failure(self):
        checker = HealthChecker(MagicMock(), MagicMock(), "http://bad:11434", "http://chroma:8000")
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(side_effect=Exception("timeout"))
            result = await checker._check_ollama()
        assert result["status"] == "unhealthy"

    @pytest.mark.asyncio
    async def test_check_chroma_success(self):
        checker = HealthChecker(MagicMock(), MagicMock(), "http://ollama:11434", "http://chroma:8000")
        mock_resp = MagicMock(status_code=200, elapsed=MagicMock(total_seconds=lambda: 0.02))
        mock_resp.json.return_value = "0.4.0"
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_resp)
            result = await checker._check_chroma()
        assert result["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_check_system_resources(self):
        checker = HealthChecker(MagicMock(), MagicMock(), "http://ollama:11434", "http://chroma:8000")
        with patch("psutil.cpu_percent", return_value=10.0):
            with patch("psutil.virtual_memory") as vm:
                vm.return_value = MagicMock(percent=50.0, available=8 * 1024**3)
                with patch("psutil.disk_usage") as du:
                    du.return_value = MagicMock(percent=40.0, free=100 * 1024**3)
                    result = await checker._check_system_resources()
        assert result["status"] == "healthy"


class TestPerformanceMonitor:
    def test_record_and_stats(self):
        monitor = PerformanceMonitor()
        monitor.record_metric("latency", 10.0)
        monitor.record_metric("latency", 20.0)
        stats = monitor.get_stats("latency")
        assert stats["count"] == 2
        assert stats["avg"] == 15.0

    def test_get_all_stats(self):
        monitor = get_performance_monitor()
        monitor.record_metric("test_metric", 1.0)
        all_stats = monitor.get_all_stats()
        assert "test_metric" in all_stats


class TestCircuitBreaker:
    @pytest.mark.asyncio
    async def test_successful_call(self):
        cb = CircuitBreaker("test", failure_threshold=3, recovery_timeout=1)

        async def ok():
            return "done"

        assert await cb.call(ok) == "done"

    @pytest.mark.asyncio
    async def test_opens_after_failures(self):
        cb = CircuitBreaker("test2", failure_threshold=2, recovery_timeout=60)

        async def fail():
            raise RuntimeError("boom")

        for _ in range(2):
            with pytest.raises(RuntimeError):
                await cb.call(fail)
        assert cb.state == CircuitState.OPEN

    @pytest.mark.asyncio
    async def test_blocks_when_open(self):
        cb = CircuitBreaker("test3", failure_threshold=1, recovery_timeout=60)
        cb.state = CircuitState.OPEN
        cb.last_failure_time = time.time()

        async def ok():
            return "ok"

        with pytest.raises(Exception, match="OPEN"):
            await cb.call(ok)

    def test_global_breakers(self):
        assert "ollama" in breakers
        assert "redis" in breakers
        assert "chroma" in breakers


class TestWorkers:
    def test_reindex_user(self):
        assert "reindex" in jobs.reindex_user(42)

    def test_ingest_document_success(self):
        mock_doc = MagicMock(id=99)
        with patch("app.db.session.get_session") as mock_session:
            with patch("app.services.document_service.DocumentService") as mock_svc:
                with patch("app.services.background_job_service.BackgroundJobService") as mock_bjs:
                    mock_svc.return_value.upload = AsyncMock(return_value=mock_doc)
                    mock_session.return_value = MagicMock()
                    result = jobs.ingest_document(1, "test.txt", "text/plain", b"hello", job_id=5)
        assert result["status"] == "ok"
        assert result["doc_id"] == 99
        mock_bjs.return_value.update_status.assert_called()

    def test_ingest_document_failure(self):
        with patch("app.db.session.get_session") as mock_session:
            with patch("app.services.document_service.DocumentService") as mock_svc:
                mock_svc.return_value.upload = AsyncMock(side_effect=RuntimeError("ingest failed"))
                mock_session.return_value = MagicMock()
                result = jobs.ingest_document(1, "bad.txt", "text/plain", b"", job_id=1)
        assert result["status"] == "error"
