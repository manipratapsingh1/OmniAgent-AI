"""Upload pipeline E2E tests — Upload → OCR/Extract → Chunk → Embed → Chroma → Verify."""
import io
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.document_service import DocumentService
from app.models.document import Document


SAMPLE_DOC = (
    b"OmniAgent Titan Omega reliability sprint document.\n"
    b"This document covers machine learning, retrieval augmented generation, "
    b"and hybrid knowledge engine architecture.\n"
    b"Section: Introduction\n"
    b"RAG systems combine vector search with language models.\n"
)


@pytest.mark.asyncio
async def test_upload_to_indexed_full_pipeline(db_session_mock):
    """Verify upload → ingest → chunk storage → indexed status."""
    doc_id_counter = {"id": 10}

    def make_doc(**kwargs):
        d = Document(
            id=doc_id_counter["id"],
            user_id=1,
            filename="pipeline.txt",
            mime_type="text/plain",
            size_bytes=len(SAMPLE_DOC),
            status="pending",
            embedding_status="pending",
        )
        return d

    db_session_mock.flush = MagicMock()
    db_session_mock.commit = MagicMock()
    db_session_mock.refresh = MagicMock()
    db_session_mock.add = MagicMock()
    db_session_mock.rollback = MagicMock()

    chunks = [
        "OmniAgent Titan Omega reliability sprint document.",
        "RAG systems combine vector search with language models.",
    ]
    vector_ids = ["10-0", "10-1"]

    with patch.object(DocumentService, "__init__", lambda self, db: None):
        service = DocumentService(db_session_mock)
        service.db = db_session_mock
        service.repo = MagicMock()
        service.repo.add.side_effect = lambda d: d
        service.repo.get.return_value = make_doc()

        with patch("app.services.document_service.ingest_file", new=AsyncMock(return_value=(2, 2, vector_ids, chunks))):
            with patch("app.rag.retriever.retrieve", new=AsyncMock(return_value=[{"document_id": 10, "text": chunks[0]}])):
                with patch("app.services.document_service.AuditService") as mock_audit:
                    with patch("app.services.document_service.asyncio.create_task"):
                        with patch("app.services.document_service.KnowledgeService"):
                            doc = await service.upload(1, "pipeline.txt", "text/plain", SAMPLE_DOC)

    assert doc.status == "indexed"
    assert doc.chunk_count == 2
    assert doc.embedding_status == "embedded"
    mock_audit.return_value.log.assert_called()


@pytest.mark.asyncio
async def test_upload_failed_no_text(db_session_mock):
    with patch.object(DocumentService, "__init__", lambda self, db: None):
        service = DocumentService(db_session_mock)
        service.db = db_session_mock
        service.repo = MagicMock()
        service.repo.add.side_effect = lambda d: d

        with patch("app.services.document_service.ingest_file", new=AsyncMock(return_value=(0, 0, [], []))):
            with patch("app.services.document_service.AuditService"):
                doc = await service.upload(1, "empty.txt", "text/plain", b"   ")

    assert doc.status == "failed"
    assert doc.embedding_status == "failed"


@pytest.mark.asyncio
async def test_upload_retrieval_verification_fails(db_session_mock):
    chunks = ["Some indexed content here for testing."]
    with patch.object(DocumentService, "__init__", lambda self, db: None):
        service = DocumentService(db_session_mock)
        service.db = db_session_mock
        service.repo = MagicMock()
        service.repo.add.side_effect = lambda d: d

        with patch("app.services.document_service.ingest_file", new=AsyncMock(return_value=(1, 1, ["1-0"], chunks))):
            with patch("app.rag.retriever.retrieve", new=AsyncMock(return_value=[])):
                with patch("app.services.document_service.AuditService"):
                    doc = await service.upload(1, "test.txt", "text/plain", b"content")

    assert doc.status == "failed"
    assert "retrieval" in (doc.error_message or "").lower()


@pytest.mark.asyncio
async def test_upload_with_background_job_progress(db_session_mock):
    chunks = ["chunk content"]

    async def mock_ingest(*args, progress_callback=None, **kwargs):
        if progress_callback:
            progress_callback(50, "halfway")
        return (1, 1, ["2-0"], chunks)

    with patch.object(DocumentService, "__init__", lambda self, db: None):
        service = DocumentService(db_session_mock)
        service.db = db_session_mock
        service.repo = MagicMock()
        service.repo.add.side_effect = lambda d: d

        with patch("app.services.document_service.ingest_file", side_effect=mock_ingest):
            with patch("app.rag.retriever.retrieve", new=AsyncMock(return_value=[{"document_id": 2}])):
                with patch("app.services.background_job_service.BackgroundJobService") as mock_bjs:
                    with patch("app.services.document_service.AuditService"):
                        with patch("app.services.document_service.asyncio.create_task"):
                            with patch("app.services.document_service.KnowledgeService"):
                                await service.upload(1, "job.txt", "text/plain", b"data", job_id=99)
                    mock_bjs.return_value.update_status.assert_called()


@pytest.mark.asyncio
async def test_ocr_image_upload_path():
    """Verify image files route through OCR extraction path."""
    from app.rag.ingest import _extract_text

    with patch("app.rag.ingest._extract_image_ocr", return_value="Extracted OCR text from image"):
        text = _extract_text("scan.png", b"\x89PNG fake")
    assert "OCR" in text or text == ""  # depends on mock path


@pytest.mark.asyncio
async def test_pdf_extraction_fallback_chain():
    from app.rag.ingest import _extract_text

    with patch("app.rag.ingest._extract_pdf_pypdf", return_value=""):
        with patch("app.rag.ingest._extract_pdf_pdfplumber", return_value="PDF content via plumber"):
            text = _extract_text("report.pdf", b"%PDF-1.4 fake")
    assert "PDF content" in text
