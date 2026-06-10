
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.document_service import DocumentService
from app.services.fast_chat_service import FastChatService
from app.services.memory_service import MemoryService
from app.models.document import Document
from app.models.user import User

@pytest.mark.asyncio
async def test_document_service_list(db_session_mock):
    service = DocumentService(db_session_mock)
    db_session_mock.exec.return_value.all.return_value = [
        Document(id=1, filename="test.pdf", user_id=1, status="indexed")
    ]
    docs = service.list_for_user(1)
    assert len(docs) == 1
    assert docs[0].filename == "test.pdf"

from app.schemas.chat import ChatRequest

@pytest.mark.asyncio
async def test_memory_service_add(db_session_mock):
    service = MemoryService(db_session_mock)
    with patch("app.services.memory_service.MemoryEntry") as mock_entry:
        service.store_short_term(1, "User likes coffee")
        assert db_session_mock.add.called
        assert db_session_mock.commit.called

@pytest.mark.asyncio
async def test_fast_chat_service_simple(db_session_mock):
    service = FastChatService(db_session_mock)
    req = ChatRequest(message="Hi", model="llama3.2")
    with patch("app.services.fast_chat_service.ollama") as mock_ollama:
        mock_ollama.generate = AsyncMock(return_value="Hello there!")
        # Mock _ensure_conversation to return a dummy conversation
        mock_conv = MagicMock(id=1, title="New Conversation")
        service._ensure_conversation = MagicMock(return_value=mock_conv)
        # Mock refresh to set ID
        def mock_refresh(obj):
            if hasattr(obj, "id"):
                obj.id = 123
        db_session_mock.refresh.side_effect = mock_refresh
        # Mock mem_append
        with patch("app.services.fast_chat_service.mem_append", new_callable=AsyncMock):
            resp = await service.chat(user_id=1, req=req)
            assert resp.content == "Hello there!"
            assert resp.message_id == 123
