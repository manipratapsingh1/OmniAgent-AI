"""API integration tests — auth, authorization, documents, chat, memory, tasks."""
import io
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.deps import current_user, require_admin
from app.models.user import User
from app.core.security import hash_password, create_access_token, create_refresh_token


class TestAuthenticationAPI:
    def test_signup_returns_tokens(self, client, unique_email):
        r = client.post(
            "/api/v1/auth/signup",
            json={"email": unique_email, "password": "securepass123", "full_name": "New User"},
        )
        assert r.status_code == 200
        data = r.json()
        assert "access_token" in data
        assert "refresh_token" in data

    def test_signup_duplicate_email(self, client, unique_email):
        payload = {"email": unique_email, "password": "securepass123"}
        client.post("/api/v1/auth/signup", json=payload)
        r = client.post("/api/v1/auth/signup", json=payload)
        assert r.status_code == 400

    def test_signup_weak_password(self, client, unique_email):
        r = client.post(
            "/api/v1/auth/signup",
            json={"email": unique_email, "password": "abc"},
        )
        assert r.status_code in (400, 422)

    def test_login_invalid_credentials(self, client):
        r = client.post(
            "/api/v1/auth/login",
            json={"email": "nobody@example.com", "password": "wrongpassword123"},
        )
        assert r.status_code == 401

    def test_me_requires_auth(self, client):
        r = client.get("/api/v1/auth/me")
        assert r.status_code == 401

    def test_me_with_valid_token(self, client, auth_headers):
        r = client.get("/api/v1/auth/me", headers=auth_headers)
        assert r.status_code == 200
        assert "email" in r.json()

    def test_refresh_token(self, client, unique_email):
        password = "securepass123"
        client.post("/api/v1/auth/signup", json={"email": unique_email, "password": password})
        login = client.post("/api/v1/auth/login", json={"email": unique_email, "password": password})
        refresh = login.json()["refresh_token"]
        r = client.post("/api/v1/auth/refresh", params={"refresh_token": refresh})
        assert r.status_code == 200
        assert "access_token" in r.json()

    def test_refresh_invalid_token(self, client):
        r = client.post("/api/v1/auth/refresh", params={"refresh_token": "invalid.token.here"})
        assert r.status_code == 401

    def test_change_password(self, client, auth_headers, unique_email):
        r = client.post(
            "/api/v1/auth/change-password",
            headers=auth_headers,
            json={"current_password": "securepass123", "new_password": "newsecurepass456"},
        )
        assert r.status_code == 200
        login = client.post(
            "/api/v1/auth/login",
            json={"email": unique_email, "password": "newsecurepass456"},
        )
        assert login.status_code == 200


class TestAuthorizationAPI:
    def test_admin_dashboard_requires_admin(self, client, normal_user):
        from app.main import app

        app.dependency_overrides[current_user] = lambda: normal_user
        try:
            r = client.get("/api/v1/admin/dashboard")
            assert r.status_code in (401, 403)
        finally:
            app.dependency_overrides.clear()

    def test_admin_dashboard_allows_admin(self, client, admin_user):
        from app.main import app

        app.dependency_overrides[current_user] = lambda: admin_user
        try:
            r = client.get("/api/v1/admin/dashboard")
            assert r.status_code == 200
        finally:
            app.dependency_overrides.clear()

    def test_protected_route_rejects_invalid_token(self, client):
        r = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalidtoken"},
        )
        assert r.status_code == 401


class TestDocumentUploadAPI:
    def test_upload_requires_auth(self, client):
        r = client.post(
            "/api/v1/documents/upload",
            files={"file": ("test.txt", io.BytesIO(b"hello"), "text/plain")},
        )
        assert r.status_code == 401

    def test_upload_text_file(self, client, auth_headers):
        from app.models.document import Document

        content = b"OmniAgent test document about machine learning and neural networks."
        mock_doc = Document(
            id=1,
            user_id=1,
            filename="test.txt",
            mime_type="text/plain",
            size_bytes=len(content),
            status="indexed",
            embedding_status="embedded",
            chunk_count=1,
        )

        with patch("app.api.v1.document.DocumentService") as mock_svc:
            mock_svc.return_value.upload = AsyncMock(return_value=mock_doc)
            r = client.post(
                "/api/v1/documents/upload",
                headers=auth_headers,
                files={"file": ("test.txt", io.BytesIO(content), "text/plain")},
            )
        assert r.status_code == 200

    def test_upload_rejects_invalid_extension(self, client, auth_headers):
        r = client.post(
            "/api/v1/documents/upload",
            headers=auth_headers,
            files={"file": ("malware.exe", io.BytesIO(b"bad"), "application/octet-stream")},
        )
        assert r.status_code in (400, 422)

    def test_list_documents(self, client, auth_headers):
        with patch("app.api.v1.document.DocumentService") as mock_svc:
            mock_svc.return_value.list_for_user.return_value = []
            r = client.get("/api/v1/documents/", headers=auth_headers)
        assert r.status_code == 200


class TestChatAPI:
    def test_chat_requires_auth(self, client):
        r = client.post("/api/v1/chat/", json={"message": "Hello"})
        assert r.status_code == 401

    def test_chat_endpoint(self, client, auth_headers):
        mock_response = MagicMock(
            content="Hello!",
            message_id=1,
            conversation_id=1,
            model="llama3.2",
            sources=[],
            citations=[],
        )
        with patch("app.api.v1.chat.FastChatService") as mock_svc:
            mock_svc.return_value.chat = AsyncMock(return_value=mock_response)
            r = client.post(
                "/api/v1/chat/",
                headers=auth_headers,
                json={"message": "Hello", "model": "llama3.2"},
            )
        assert r.status_code == 200


class TestMemoryAPI:
    def test_memory_list_requires_auth(self, client):
        r = client.get("/api/v1/memory/short-term")
        assert r.status_code == 401

    def test_memory_store(self, client, auth_headers):
        from datetime import datetime, timezone

        mock_entry = MagicMock(
            id=1,
            memory_type="short_term",
            content="test",
            created_at=datetime.now(timezone.utc),
        )
        with patch("app.api.v1.memory.MemoryService") as mock_svc:
            mock_svc.return_value.store_short_term.return_value = mock_entry
            r = client.post(
                "/api/v1/memory",
                headers=auth_headers,
                json={"content": "User prefers dark mode", "memory_type": "short_term"},
            )
        assert r.status_code == 200


class TestTasksAPI:
    def test_tasks_list(self, client, auth_headers):
        r = client.get("/api/v1/tasks/", headers=auth_headers)
        assert r.status_code == 200

    def test_create_task(self, client, auth_headers):
        r = client.post(
            "/api/v1/tasks/",
            headers=auth_headers,
            json={"title": "Test task", "description": "Do something"},
        )
        assert r.status_code in (200, 201)


class TestHealthAndMetrics:
    def test_healthz(self, client):
        assert client.get("/healthz").status_code == 200

    def test_readiness(self, client):
        r = client.get("/api/v1/health/readyz")
        assert r.status_code in (200, 503)

    def test_metrics_endpoint(self, client):
        r = client.get("/metrics")
        assert r.status_code in (200, 404)
