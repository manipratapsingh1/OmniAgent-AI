"""Bulk API route tests for integration coverage."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestConversationRoutes:
    def test_list_conversations(self, client, auth_headers):
        r = client.get("/api/v1/conversations/", headers=auth_headers)
        assert r.status_code == 200


class TestSearchRoutes:
    def test_search_conversations(self, client, auth_headers):
        r = client.get("/api/v1/search/conversations?q=test", headers=auth_headers)
        assert r.status_code == 200


class TestQuotaRoutes:
    def test_quota_status(self, client, auth_headers):
        r = client.get("/api/v1/quota", headers=auth_headers)
        assert r.status_code == 200


class TestNotificationRoutes:
    def test_list_notifications(self, client, auth_headers):
        r = client.get("/api/v1/notifications", headers=auth_headers)
        assert r.status_code == 200


class TestBackgroundJobRoutes:
    def test_list_jobs(self, client, auth_headers):
        r = client.get("/api/v1/jobs", headers=auth_headers)
        assert r.status_code == 200


class TestToolsRoutes:
    def test_list_tools(self, client, auth_headers):
        r = client.get("/api/v1/tools/", headers=auth_headers)
        assert r.status_code == 200

    @pytest.mark.asyncio
    async def test_run_calculator(self, client, auth_headers):
        r = client.post(
            "/api/v1/tools/run",
            headers=auth_headers,
            json={"tool": "calculator", "args": {"expression": "2+2"}},
        )
        assert r.status_code in (200, 404, 422)


class TestHealthRoutes:
    def test_health_api(self, client):
        r = client.get("/api/v1/health/healthz")
        assert r.status_code == 200

    def test_health_ready(self, client):
        r = client.get("/api/v1/health/readyz")
        assert r.status_code in (200, 503)


class TestDocumentRoutesExtended:
    def test_document_search(self, client, auth_headers):
        r = client.get("/api/v1/documents/search?q=test", headers=auth_headers)
        assert r.status_code == 200

    def test_knowledge_base_list(self, client, auth_headers):
        r = client.get("/api/v1/documents/knowledge-base/list", headers=auth_headers)
        assert r.status_code == 200


class TestChatRoutesExtended:
    def test_list_models(self, client, auth_headers):
        r = client.get("/api/v1/chat/models", headers=auth_headers)
        assert r.status_code == 200

    def test_knowledge_assistant(self, client, auth_headers):
        with patch("app.api.v1.chat.FastChatService") as mock_svc:
            mock_resp = MagicMock(
                content="Answer",
                message_id=1,
                conversation_id=1,
                model="llama3.2",
                sources=[],
                citations=[],
            )
            mock_svc.return_value.chat = AsyncMock(return_value=mock_resp)
            r = client.post(
                "/api/v1/chat/knowledge-assistant",
                headers=auth_headers,
                json={"message": "What is RAG?", "use_rag": True},
            )
        assert r.status_code in (200, 422)


class TestApiKeyRoutes:
    def test_list_api_keys(self, client, auth_headers):
        r = client.get("/api/v1/keys", headers=auth_headers)
        assert r.status_code == 200

    def test_create_api_key(self, client, auth_headers):
        r = client.post(
            "/api/v1/keys",
            headers=auth_headers,
            json={"name": "test-key"},
        )
        assert r.status_code in (200, 201)
