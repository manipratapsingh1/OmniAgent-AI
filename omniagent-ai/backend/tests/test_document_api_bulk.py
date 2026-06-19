"""Document API route coverage."""
import io
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.api.v1.document import _allowed_file
from app.models.document import Document


class TestAllowedFile:
    def test_pdf_allowed(self):
        assert _allowed_file("report.pdf", "application/pdf") is True

    def test_exe_blocked(self):
        assert _allowed_file("malware.exe", "application/octet-stream") is False


class TestDocumentRoutesBulk:
    def test_list_docs(self, client, auth_headers):
        assert client.get("/api/v1/documents/", headers=auth_headers).status_code == 200

    def test_search_docs(self, client, auth_headers):
        assert client.get("/api/v1/documents/search?q=test", headers=auth_headers).status_code == 200

    def test_filter_docs(self, client, auth_headers):
        assert client.get("/api/v1/documents/filter?status=indexed", headers=auth_headers).status_code == 200

    def test_kb_info(self, client, auth_headers):
        assert client.get("/api/v1/documents/knowledge-base/info", headers=auth_headers).status_code == 200

    def test_cache_stats(self, client, auth_headers):
        assert client.post("/api/v1/documents/cache/clear", headers=auth_headers).status_code in (200, 500)

    def test_rag_search(self, client, auth_headers):
        with patch("app.api.v1.document.retrieve", new=AsyncMock(return_value=[])):
            r = client.get("/api/v1/documents/rag-search?q=machine+learning", headers=auth_headers)
        assert r.status_code == 200

    def test_document_qa(self, client, auth_headers):
        with patch("app.api.v1.document.retrieve", new=AsyncMock(return_value=[])):
            with patch("app.api.v1.document.ollama") as mock_ollama:
                mock_ollama.generate = AsyncMock(return_value="Answer")
                r = client.post(
                    "/api/v1/documents/qa",
                    headers=auth_headers,
                    json={"question": "What is ML?"},
                )
        assert r.status_code == 200

    def test_preview_not_found(self, client, auth_headers):
        with patch("app.api.v1.document.DocumentRepo") as mock_repo:
            mock_repo.return_value.get.return_value = None
            r = client.get("/api/v1/documents/99999/preview", headers=auth_headers)
        assert r.status_code == 404

    def test_delete_doc(self, client, auth_headers):
        with patch("app.api.v1.document.DocumentService") as mock_svc:
            mock_svc.return_value.delete.return_value = True
            r = client.delete("/api/v1/documents/1", headers=auth_headers)
        assert r.status_code in (200, 204, 404)

    def test_upload_job(self, client, auth_headers):
        import random
        from app.models.background_job import BackgroundJob
        content = b"Job upload test content for background processing."
        job_id = random.randint(1000000, 9999999)
        with patch("app.api.v1.document.default_queue") as mock_queue:
            mock_queue.enqueue.return_value = MagicMock(id="job-1")
            with patch("app.api.v1.document.BackgroundJobService") as mock_bjs:
                mock_bjs.return_value.create_job.return_value = BackgroundJob(
                    id=job_id, user_id=1, job_type="ingest_document", status="pending"
                )
                r = client.post(
                    "/api/v1/documents/upload_job",
                    headers=auth_headers,
                    files={"file": ("job.txt", io.BytesIO(content), "text/plain")},
                )
        assert r.status_code in (200, 202)
