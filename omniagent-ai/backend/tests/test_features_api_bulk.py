"""Features API route coverage."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestFeaturesRoutes:
    def test_get_categories(self, client, auth_headers):
        r = client.get("/api/v1/features/categories", headers=auth_headers)
        assert r.status_code == 200

    def test_get_templates(self, client, auth_headers):
        r = client.get("/api/v1/features/templates", headers=auth_headers)
        assert r.status_code == 200

    def test_hybrid_knowledge_status(self, client, auth_headers):
        r = client.get("/api/v1/features/hybrid-knowledge/status", headers=auth_headers)
        assert r.status_code == 200

    def test_feedback_summary(self, client, auth_headers):
        r = client.get("/api/v1/features/feedback/summary", headers=auth_headers)
        assert r.status_code in (200, 403)

    def test_usage_analytics(self, client, auth_headers):
        r = client.get("/api/v1/features/analytics/usage", headers=auth_headers)
        assert r.status_code in (200, 403)

    def test_knowledge_graph(self, client, auth_headers):
        r = client.get("/api/v1/features/knowledge-graph", headers=auth_headers)
        assert r.status_code == 200

    def test_get_document_tags(self, client, auth_headers):
        r = client.get("/api/v1/features/document/1/tags", headers=auth_headers)
        assert r.status_code == 200

    def test_create_category(self, client, auth_headers):
        r = client.post(
            "/api/v1/features/categories",
            headers=auth_headers,
            json={"name": "Science", "description": "Science docs"},
        )
        assert r.status_code in (200, 201, 403)

    def test_deep_research(self, client, auth_headers):
        with patch("app.api.v1.features.DeepResearchService", create=True) as mock_svc:
            mock_svc.return_value.research = AsyncMock(return_value={
                "query": "AI",
                "report": "Research report",
                "executive_summary": "Summary",
                "sources": {"documents": [], "web": []},
                "citation_accuracy": {},
                "knowledge_case": "case_3_no_document",
                "confidence": "none",
                "provider_used": "ollama",
                "generated_at": "2026-01-01",
                "elapsed_ms": 100,
            })
            r = client.post(
                "/api/v1/features/deep-research",
                headers=auth_headers,
                json={"query": "Latest AI trends"},
            )
        assert r.status_code == 200

    def test_export_conversation(self, client, auth_headers):
        msg = MagicMock(role="user", content="Hi", sources=None, created_at=MagicMock(isoformat=lambda: "2026-01-01"))
        with patch("app.api.v1.features.db_session") as _:
            pass
        with patch("sqlmodel.Session.exec") as _:
            pass
        # Patch at route level via db returning messages
        from app.models.message import Message
        from datetime import datetime, timezone

        mock_msg = Message(id=1, conversation_id=1, role="user", content="Hi", created_at=datetime.now(timezone.utc))
        with patch.object(client.app.state, "_state", create=True):
            pass

        # Use dependency override for simpler path
        from app.main import app
        from app.deps import db_session

        mock_db = MagicMock()
        mock_db.exec.return_value.all.return_value = [mock_msg]

        def override_db():
            yield mock_db

        app.dependency_overrides[db_session] = override_db
        try:
            r = client.get("/api/v1/features/export/conversation/1?format=markdown", headers=auth_headers)
            assert r.status_code == 200
        finally:
            app.dependency_overrides.clear()

    def test_study_materials(self, client, auth_headers):
        r = client.get("/api/v1/features/study-materials?document_id=1", headers=auth_headers)
        assert r.status_code in (200, 422)

    def test_tag_search(self, client, auth_headers):
        r = client.get("/api/v1/features/tags/search?tag=finance", headers=auth_headers)
        assert r.status_code in (200, 422)
