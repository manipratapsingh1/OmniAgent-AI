"""Fast chat service coverage tests."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.schemas.chat import ChatRequest
from app.services.ai.hybrid_knowledge_engine import KnowledgeCase, KnowledgeMode
from app.services.fast_chat_service import FastChatService


def _make_knowledge_result(chunks=None):
    return {
        "case": KnowledgeCase.FULL_DOCUMENT,
        "mode": KnowledgeMode.AUTO,
        "chunks": chunks or [{"document_id": 1, "chunk_index": 0, "text": "evidence text", "score": 0.8}],
        "confidence": "high",
        "context_text": "evidence",
        "system_instructions": "cite sources",
        "memory_context": [],
        "web_results": [],
        "metadata": {},
    }


@pytest.fixture
def fast_chat(db_session_mock):
    service = FastChatService(db_session_mock)
    conv = MagicMock(id=1, title="Chat", model="llama3.2", user_id=1)
    service._ensure_conversation = MagicMock(return_value=conv)
    db_session_mock.refresh = MagicMock(side_effect=lambda o: setattr(o, "id", 42) if hasattr(o, "id") else None)
    return service


class TestFastChatService:
    @pytest.mark.asyncio
    async def test_chat_ai_only(self, fast_chat, db_session_mock):
        with patch("app.services.fast_chat_service.ollama") as mock_ollama:
            mock_ollama.generate = AsyncMock(return_value="Direct answer")
            with patch("app.services.fast_chat_service.mem_append", new=AsyncMock()):
                with patch.object(fast_chat.memory, "get_learned_facts", return_value=[]):
                    resp = await fast_chat.chat(1, ChatRequest(message="Hello", use_rag=False))
        assert resp.content == "Direct answer"

    @pytest.mark.asyncio
    async def test_chat_with_rag(self, fast_chat):
        with patch.object(fast_chat.knowledge_engine, "retrieve_and_decide", new=AsyncMock(return_value=_make_knowledge_result())):
            with patch.object(fast_chat.knowledge_engine, "build_prompt", return_value=("prompt", "system")):
                with patch.object(fast_chat.knowledge_engine, "enrich_citations", side_effect=lambda x: x):
                    with patch("app.services.fast_chat_service.ollama") as mock_ollama:
                        mock_ollama.generate = AsyncMock(return_value="Answer [doc:1#0]")
                        with patch("app.services.fast_chat_service.mem_append", new=AsyncMock()):
                            with patch.object(fast_chat.memory, "get_learned_facts", return_value=[]):
                                resp = await fast_chat.chat(1, ChatRequest(message="What is ML?", use_rag=True))
        assert "Answer" in resp.content

    @pytest.mark.asyncio
    async def test_chat_retrieval_failure_fallback(self, fast_chat):
        with patch.object(fast_chat.knowledge_engine, "retrieve_and_decide", new=AsyncMock(side_effect=RuntimeError("retrieval failed"))):
            with patch("app.services.fast_chat_service.ollama") as mock_ollama:
                mock_ollama.generate = AsyncMock(return_value="Fallback answer")
                with patch("app.services.fast_chat_service.mem_append", new=AsyncMock()):
                    with patch.object(fast_chat.memory, "get_learned_facts", return_value=[]):
                        resp = await fast_chat.chat(1, ChatRequest(message="Hi", use_rag=True))
        assert resp.content

    @pytest.mark.asyncio
    async def test_chat_generation_error(self, fast_chat):
        with patch("app.services.fast_chat_service.ollama") as mock_ollama:
            mock_ollama.generate = AsyncMock(side_effect=RuntimeError("ollama down"))
            with patch("app.services.fast_chat_service.mem_append", new=AsyncMock()):
                with patch.object(fast_chat.memory, "get_learned_facts", return_value=[]):
                    resp = await fast_chat.chat(1, ChatRequest(message="Hi", use_rag=False))
        assert "Error" in resp.content

    @pytest.mark.asyncio
    async def test_chat_empty_response(self, fast_chat):
        with patch("app.services.fast_chat_service.ollama") as mock_ollama:
            mock_ollama.generate = AsyncMock(return_value="")
            with patch("app.services.fast_chat_service.mem_append", new=AsyncMock()):
                with patch.object(fast_chat.memory, "get_learned_facts", return_value=[]):
                    resp = await fast_chat.chat(1, ChatRequest(message="Hi", use_rag=False))
        assert "couldn't generate" in resp.content.lower()

    def test_resolve_mode(self, fast_chat):
        assert fast_chat._resolve_mode(ChatRequest(message="x", use_rag=False)) == KnowledgeMode.AI_ONLY
        assert fast_chat._resolve_mode(ChatRequest(message="x", use_rag=True, knowledge_mode="documents_only")) == KnowledgeMode.DOCUMENTS_ONLY

    def test_build_citations(self, fast_chat):
        sources = [{"document_id": 1, "chunk_index": 0, "text": "content", "score": 0.8}]
        with patch.object(fast_chat.knowledge_engine, "enrich_citations", side_effect=lambda x: x):
            cites, was_cited = fast_chat._build_citations("See [doc:1#0]", sources)
        assert was_cited is True
        assert len(cites) >= 1

    @pytest.mark.asyncio
    async def test_chat_with_learned_facts(self, fast_chat):
        fact = MagicMock(fact="User likes Python")
        with patch("app.services.fast_chat_service.ollama") as mock_ollama:
            mock_ollama.generate = AsyncMock(return_value="Noted!")
            with patch("app.services.fast_chat_service.mem_append", new=AsyncMock()):
                with patch.object(fast_chat.memory, "get_learned_facts", return_value=[fact]):
                    resp = await fast_chat.chat(1, ChatRequest(message="Hi", use_rag=False))
        assert resp.content == "Noted!"

    @pytest.mark.asyncio
    async def test_chat_invalid_input_raises(self, fast_chat):
        with pytest.raises(ValueError):
            await fast_chat.chat(1, ChatRequest(message="", use_rag=False))
