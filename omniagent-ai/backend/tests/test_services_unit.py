"""Export service and utility tests."""
import pytest
from unittest.mock import MagicMock, patch


class TestExportService:
    def test_export_markdown(self):
        from app.services.export_service import ExportService

        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
        ]
        result = ExportService.export_conversation_to_markdown(messages, title="Test Chat")
        assert "# Test Chat" in result
        assert "Hello" in result
        assert "Hi there!" in result

    def test_export_json(self):
        from app.services.export_service import ExportService
        result = ExportService.export_conversation_to_json([{"role": "user", "content": "Hi"}])
        assert "messages" in result

    def test_export_csv(self):
        from app.services.export_service import ExportService
        result = ExportService.export_conversation_to_csv([{"role": "user", "content": "Hi"}])
        assert "Role" in result
        assert "user" in result


class TestCitationUtils:
    def test_validate_citation_accuracy_no_citations(self):
        from app.utils.citations import validate_citation_accuracy
        result = validate_citation_accuracy("No citations here.", [])
        assert result["citations_in_text"] == 0

    def test_get_citations_with_fallback(self):
        from app.utils.citations import get_citations_with_fallback
        answer = "Based on [doc:1#0] the policy states..."
        sources = [{"document_id": 1, "chunk_index": 0, "text": "policy text", "score": 0.8}]
        cited, was_cited = get_citations_with_fallback(answer, sources)
        assert was_cited is True
        assert len(cited) >= 1


class TestResilience:
    def test_breakers_exist(self):
        from app.utils.resilience import breakers
        assert "ollama" in breakers
