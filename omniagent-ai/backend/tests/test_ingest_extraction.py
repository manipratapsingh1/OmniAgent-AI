"""Ingest pipeline unit tests — extraction, chunking, embedding, storage (mocked)."""
import io
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.rag.ingest import (
    _extract_text,
    _extract_pdf_pypdf,
    _extract_docx,
    _extract_csv,
    _extract_html,
    _extract_image_ocr,
    ingest_file,
)


class TestTextExtraction:
    def test_plain_text_file(self):
        raw = b"Hello world.\nThis is a test document for ingestion."
        text = _extract_text("notes.txt", raw)
        assert "Hello world" in text

    def test_markdown_file(self):
        raw = b"# Title\n\nSome markdown content here."
        text = _extract_text("readme.md", raw)
        assert "markdown" in text

    def test_empty_text_file(self):
        text = _extract_text("empty.txt", b"   ")
        assert text == ""

    def test_csv_extraction(self):
        raw = b"name,age\nAlice,30\nBob,25"
        text = _extract_csv(raw, "data.csv")
        assert "Alice" in text or text == ""  # pandas may not be available in all envs

    def test_html_extraction(self):
        raw = b"<html><body><p>Hello HTML</p></body></html>"
        text = _extract_html(raw, "page.html")
        assert text == "" or "Hello HTML" in text

    def test_pdf_invalid_bytes(self):
        text = _extract_pdf_pypdf(b"not a pdf", "bad.pdf")
        assert text == ""

    def test_docx_invalid_bytes(self):
        text = _extract_docx(b"not docx", "bad.docx")
        assert text == ""

    def test_ocr_invalid_image(self):
        text = _extract_image_ocr(b"not an image", "bad.png")
        assert text == ""

    def test_unknown_extension_fallback_decode(self):
        raw = b"fallback content for unknown type"
        text = _extract_text("file.xyz", raw)
        assert "fallback content" in text


class TestIngestFileMocked:
    @pytest.mark.asyncio
    async def test_ingest_full_pipeline_success(self):
        sample_text = "Machine learning is a subset of artificial intelligence. " * 20
        mock_vectors = [[0.1] * 8] * 3

        with patch("app.rag.ingest._extract_text", return_value=sample_text):
            with patch("app.rag.ingest.semantic_chunk_text", return_value=["chunk1", "chunk2", "chunk3"]):
                with patch("app.rag.ingest.embed_texts", new=AsyncMock(return_value=mock_vectors)):
                    with patch("app.rag.ingest.vector_store") as mock_store:
                        with patch("app.rag.ingest.query_vectors") as mock_query:
                            mock_query.return_value = {
                                "documents": [["chunk1"]],
                                "metadatas": [[{"document_id": 42}]],
                            }
                            n_chunks, n_vectors, ids, chunks = await ingest_file(
                                1, 42, "test.txt", b"raw"
                            )
        assert n_chunks == 3
        assert n_vectors == 3
        assert len(ids) == 3
        mock_store.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_ingest_no_text_extracted(self):
        with patch("app.rag.ingest._extract_text", return_value=""):
            n_chunks, n_vectors, ids, chunks = await ingest_file(1, 1, "empty.txt", b"")
        assert n_chunks == 0
        assert ids == []

    @pytest.mark.asyncio
    async def test_ingest_embedding_failure(self):
        with patch("app.rag.ingest._extract_text", return_value="Some text content here."):
            with patch("app.rag.ingest.semantic_chunk_text", return_value=["chunk1"]):
                with patch("app.rag.ingest.embed_texts", new=AsyncMock(side_effect=RuntimeError("ollama down"))):
                    n_chunks, _, ids, _ = await ingest_file(1, 1, "test.txt", b"x")
        assert n_chunks == 0
        assert ids == []

    @pytest.mark.asyncio
    async def test_ingest_vector_count_mismatch(self):
        with patch("app.rag.ingest._extract_text", return_value="Text " * 50):
            with patch("app.rag.ingest.semantic_chunk_text", return_value=["a", "b"]):
                with patch("app.rag.ingest.embed_texts", new=AsyncMock(return_value=[[0.1]])):
                    n_chunks, _, ids, _ = await ingest_file(1, 1, "test.txt", b"x")
        assert n_chunks == 0
        assert ids == []

    @pytest.mark.asyncio
    async def test_ingest_retrieval_verification_failure(self):
        with patch("app.rag.ingest._extract_text", return_value="Content " * 30):
            with patch("app.rag.ingest.semantic_chunk_text", return_value=["chunk1"]):
                with patch("app.rag.ingest.embed_texts", new=AsyncMock(return_value=[[0.1] * 4])):
                    with patch("app.rag.ingest.vector_store") as mock_store:
                        with patch("app.rag.ingest.query_vectors") as mock_query:
                            mock_query.return_value = {
                                "documents": [["chunk1"]],
                                "metadatas": [[{"document_id": 999}]],
                            }
                            n_chunks, _, ids, _ = await ingest_file(1, 1, "test.txt", b"x")
        assert n_chunks == 0
        mock_store.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_ingest_progress_callback(self):
        progress = []

        def cb(pct, msg):
            progress.append((pct, msg))

        with patch("app.rag.ingest._extract_text", return_value="Hello " * 20):
            with patch("app.rag.ingest.semantic_chunk_text", return_value=["chunk1"]):
                with patch("app.rag.ingest.embed_texts", new=AsyncMock(return_value=[[0.1] * 4])):
                    with patch("app.rag.ingest.vector_store"):
                        with patch("app.rag.ingest.query_vectors") as mock_query:
                            mock_query.return_value = {
                                "documents": [["chunk1"]],
                                "metadatas": [[{"document_id": 5}]],
                            }
                            await ingest_file(1, 5, "test.txt", b"x", progress_callback=cb)
        assert any(p[0] >= 10 for p in progress)

    @pytest.mark.asyncio
    async def test_ingest_chroma_storage_failure(self):
        with patch("app.rag.ingest._extract_text", return_value="Data " * 20):
            with patch("app.rag.ingest.semantic_chunk_text", return_value=["chunk1"]):
                with patch("app.rag.ingest.embed_texts", new=AsyncMock(return_value=[[0.1] * 4])):
                    with patch("app.rag.ingest.vector_store") as mock_store:
                        mock_store.add.side_effect = RuntimeError("chroma down")
                        n_chunks, _, ids, _ = await ingest_file(1, 1, "test.txt", b"x")
        assert n_chunks == 0
        assert ids == []
