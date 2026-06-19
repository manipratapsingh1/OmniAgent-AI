import pytest
import time
from unittest.mock import AsyncMock, MagicMock, patch
from app.utils.resilience import CircuitBreaker, CircuitState


@pytest.mark.asyncio
async def test_circuit_breaker_flow():
    cb = CircuitBreaker("test_breaker", failure_threshold=2, recovery_timeout=1)
    
    # Success path
    async def mock_success():
        return "ok"
    
    res = await cb.call(mock_success)
    assert res == "ok"
    assert cb.state == CircuitState.CLOSED
    
    # Failure path
    async def mock_fail():
        raise ValueError("error")
        
    with pytest.raises(ValueError):
        await cb.call(mock_fail)
    assert cb.failure_count == 1
    assert cb.state == CircuitState.CLOSED
    
    # 2nd failure opens circuit
    with pytest.raises(ValueError):
        await cb.call(mock_fail)
    assert cb.state == CircuitState.OPEN
    
    # Immediate calls when OPEN should raise Exception
    with pytest.raises(Exception, match="is OPEN"):
        await cb.call(mock_success)
        
    # Wait for recovery timeout to transition to HALF_OPEN
    time.sleep(1.1)
    res = await cb.call(mock_success)
    assert res == "ok"
    assert cb.state == CircuitState.CLOSED


@pytest.mark.asyncio
async def test_retriever_chroma_fallback(db_session_mock):
    # Simulate Chroma connection failure
    from app.rag.retriever import retrieve
    
    # Setup mock DB responses for the SQL fallback
    chunk = MagicMock()
    chunk.document_id = 1
    chunk.chunk_index = 0
    chunk.text = "sqlite text content"
    doc = MagicMock()
    db_session_mock.exec.return_value.all.return_value = [(chunk, doc)]
    
    with patch("app.rag.retriever.query_vectors", side_effect=Exception("Chroma Offline")):
        with patch("app.rag.retriever.get_optimized_retriever", return_value=None):
            with patch("app.cache.get_json", return_value=None):
                results = await retrieve(user_id=1, query="sqlite text", k=1, db=db_session_mock)
                
    # Verify fallback keyword results are returned
    assert len(results) == 1
    assert results[0]["text"] == "sqlite text content"


@pytest.mark.asyncio
async def test_semantic_cache_chroma_offline():
    from app.utils.semantic_cache import semantic_cache
    
    # Verify that semantic cache handles initialization/connection errors without raising exceptions
    with patch("app.utils.semantic_cache.get_vector_store", return_value=None):
        ans = await semantic_cache.get("some query")
        assert ans is None
        
        await semantic_cache.set("some query", "some answer")
        # Should complete without error
