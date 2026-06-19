"""Tests for model router, web search service, and deep research."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.ai.model_router import ModelRouter, TaskType, classify_task
from app.services.web_search_service import (
    SearchResult,
    rerank_results,
    validate_url,
    WebSearchService,
)


class TestTaskClassification:
    def test_coding_task(self):
        assert classify_task("Write a Python function to sort a list") == TaskType.CODING

    def test_research_task(self):
        assert classify_task("Research the latest AI trends") == TaskType.RESEARCH

    def test_fast_task(self):
        assert classify_task("Give me a quick summary") == TaskType.FAST

    def test_general_task(self):
        assert classify_task("Hello, how are you?") == TaskType.GENERAL


class TestModelRouter:
    @pytest.fixture
    def mock_providers(self):
        ollama = MagicMock()
        ollama.generate = AsyncMock(return_value="ollama response")
        ollama.stream = AsyncMock()
        openai = MagicMock()
        openai.generate = AsyncMock(return_value="openai response")
        return {"ollama": ollama, "openai": openai}

    @pytest.mark.asyncio
    async def test_generate_success(self, mock_providers):
        router = ModelRouter(mock_providers)
        result, provider = await router.generate("test prompt", query="hello")
        assert result == "ollama response"
        assert provider == "ollama"

    @pytest.mark.asyncio
    async def test_generate_failover(self, mock_providers):
        mock_providers["ollama"].generate = AsyncMock(side_effect=Exception("down"))
        router = ModelRouter(mock_providers)
        result, provider = await router.generate("test", query="hello", provider="ollama")
        assert result == "openai response"
        assert provider == "openai"

    def test_select_preferred_provider(self, mock_providers):
        router = ModelRouter(mock_providers)
        p, name = router.select_provider("hello", preferred="openai")
        assert name == "openai"


class TestWebSearchService:
    def test_validate_url(self):
        assert validate_url("https://example.com/page") is True
        assert validate_url("not-a-url") is False
        assert validate_url("") is False

    def test_rerank_results(self):
        results = [
            SearchResult("Low", "unrelated content", "https://a.com"),
            SearchResult("High", "machine learning algorithms", "https://b.com"),
        ]
        ranked = rerank_results(results, "machine learning")
        assert ranked[0].title == "High"
        assert ranked[0].score > ranked[1].score

    def test_search_result_to_dict(self):
        r = SearchResult("Title", "snippet text", "https://example.com", score=0.8)
        d = r.to_dict()
        assert d["title"] == "Title"
        assert d["url"] == "https://example.com"
        assert "retrieved_at" in d
        assert d["confidence_score"] == 0.8

    @pytest.mark.asyncio
    async def test_search_empty_query(self):
        service = WebSearchService()
        assert await service.search("") == []

    @pytest.mark.asyncio
    async def test_brave_search_mock(self):
        service = WebSearchService()
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "web": {
                "results": [
                    {"title": "Test", "description": "A test result", "url": "https://example.com"}
                ]
            }
        }
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get = AsyncMock(return_value=mock_response)
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value = mock_instance

            with patch("app.services.web_search_service._settings") as mock_settings:
                mock_settings.BRAVE_API_KEY = "test-key"
                mock_settings.WEB_SEARCH_MAX_RESULTS = 5
                results = await service._search_brave("test query")
                assert len(results) == 1
                assert results[0].title == "Test"
