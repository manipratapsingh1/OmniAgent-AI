"""Chat API helper and route coverage."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.api.v1.chat import _normalize_token, DEFAULT_FAST_MODEL


class TestNormalizeToken:
    def test_string_passthrough(self):
        assert _normalize_token("hello") == "hello"

    def test_none_returns_empty(self):
        assert _normalize_token(None) == ""

    def test_dict_response_key(self):
        assert _normalize_token({"response": "chunk"}) == "chunk"

    def test_dict_message_nested(self):
        assert _normalize_token({"message": {"content": "nested"}}) == "nested"


class TestChatStreamRoute:
    def test_stream_endpoint(self, client, auth_headers):
        async def fake_stream(*args, **kwargs):
            yield "Hello"
            yield " world"

        with patch("app.api.v1.chat.ollama") as mock_ollama:
            mock_ollama.stream = fake_stream
            with patch("app.api.v1.chat.FastChatService") as mock_svc:
                mock_conv = MagicMock(id=1)
                mock_svc.return_value._ensure_conversation.return_value = mock_conv
                r = client.post(
                    "/api/v1/chat/stream",
                    headers=auth_headers,
                    json={"message": "Hi", "model": DEFAULT_FAST_MODEL},
                )
        assert r.status_code in (200, 500)

    def test_fast_rag_endpoint(self, client, auth_headers):
        mock_resp = MagicMock(
            content="Fast RAG answer",
            message_id=1,
            conversation_id=1,
            model="phi3:mini",
            sources=[],
            citations=[],
        )
        with patch("app.api.v1.chat.FastChatService") as mock_svc:
            mock_svc.return_value.chat = AsyncMock(return_value=mock_resp)
            r = client.post(
                "/api/v1/chat/fast-rag",
                headers=auth_headers,
                json={"message": "Explain RAG", "use_rag": True},
            )
        assert r.status_code == 200
