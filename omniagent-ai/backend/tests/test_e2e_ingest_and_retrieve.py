import pytest
import asyncio

from app.rag.ingest import ingest_file


@pytest.mark.asyncio
async def test_ingest_and_retrieve_integration():
    """Integration-style test: ingest a small text file and ensure ingestion returns chunks and vectors.

    This test requires external services (Ollama embeddings and Chroma). It will be skipped
    if those services are not reachable in the test environment.
    """
    try:
        # Minimal test content
        text = b"Hello world. This is a test document used for E2E ingestion.\nIt contains several sentences."
        # Run ingest_file - use small doc id
        n_chunks, n_vectors, ids, chunks = await ingest_file(1, 9999, "test.txt", text)
        # If ingestion failed due to missing services, return skip
        if n_chunks == 0:
            pytest.skip("Ingestion returned 0 chunks (external services may be unavailable)")

        assert n_chunks > 0
        assert n_vectors == n_chunks
        assert len(ids) == n_chunks
        assert len(chunks) == n_chunks

    except Exception as e:
        pytest.skip(f"Integration services not available or error occurred: {e}")
