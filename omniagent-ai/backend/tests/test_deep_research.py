"""Deep research service tests."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.deep_research_service import DeepResearchService


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def mock_providers():
    provider = MagicMock()
    provider.generate = AsyncMock(return_value="Generated report")
    return {"ollama": provider}


class TestDeepResearchService:
    @pytest.mark.asyncio
    async def test_research_returns_report(self, mock_db, mock_providers):
        mock_engine = MagicMock()
        mock_engine.retrieve_and_decide = AsyncMock(return_value={
            "case": MagicMock(value="case_3_no_document"),
            "confidence": "none",
            "chunks": [],
            "context_text": "",
            "web_results": [],
        })
        mock_engine.build_prompt = MagicMock(return_value=("prompt", "instructions"))

        mock_router = MagicMock()
        mock_router.generate = AsyncMock(return_value=(
            "## Executive Summary\nML is AI subset.\n\n## Key Findings\n...",
            "ollama",
        ))

        with patch.object(DeepResearchService, "__init__", lambda self, db, providers=None: None):
            service = DeepResearchService.__new__(DeepResearchService)
            service.db = mock_db
            service.knowledge_engine = mock_engine
            service.web_search = MagicMock()
            service.web_search.search = AsyncMock(return_value=[])
            service.router = mock_router

            result = await service.research(user_id=1, query="What is ML?")

        assert "report" in result
        assert result["query"] == "What is ML?"
        assert "executive_summary" in result
        assert "citation_accuracy" in result

    def test_extract_summary(self, mock_db):
        with patch.object(DeepResearchService, "__init__", lambda self, db, providers=None: None):
            service = DeepResearchService.__new__(DeepResearchService)
            report = "## Executive Summary\nThis is the summary.\n\n## Key Findings\nDetails here."
            summary = service._extract_summary(report)
            assert "summary" in summary.lower()

    def test_extract_summary_fallback(self, mock_db):
        with patch.object(DeepResearchService, "__init__", lambda self, db, providers=None: None):
            service = DeepResearchService.__new__(DeepResearchService)
            report = "No structured sections, just content."
            summary = service._extract_summary(report)
            assert len(summary) > 0
