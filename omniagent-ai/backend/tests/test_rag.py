from app.rag.chunker import chunk_text


def test_chunker_basic():
    chunks = chunk_text("a" * 2000, size=800, overlap=100)
    assert len(chunks) >= 2
    assert all(len(c) <= 800 for c in chunks)