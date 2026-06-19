import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session
from app.main import app
from app.deps import current_user
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.user import User

@pytest.fixture
def mock_admin(admin_user):
    def get_admin():
        return admin_user
    return get_admin

@pytest.fixture
def mock_user(normal_user):
    def get_user():
        return normal_user
    return get_user


def test_debug_status_requires_admin(client: TestClient, mock_admin, mock_user):
    # 1. Access by Admin -> Success 200
    app.dependency_overrides[current_user] = mock_admin
    response = client.get("/api/v1/debug/status")
    assert response.status_code == 200
    data = response.json()
    assert "perf_metrics" in data
    assert "cache" in data
    assert "jobs" in data
    assert "memory" in data
    assert "current_user" in data
    
    # 2. Access by Regular User -> Denied 403
    app.dependency_overrides[current_user] = mock_user
    response = client.get("/api/v1/debug/status")
    assert response.status_code == 403
    
    app.dependency_overrides.clear()


def test_csp_header_contains_configured_origins(client: TestClient):
    response = client.get("/api/v1/health/healthz")
    assert "Content-Security-Policy" in response.headers
    csp = response.headers["Content-Security-Policy"]
    assert "connect-src" in csp
    # Default config CORS_ORIGINS is "http://localhost:5173"
    assert "http://localhost:5173" in csp


def test_get_shared_conversation_success(client: TestClient):
    from app.db.session import get_session
    from sqlmodel import select
    from app.models.sharing_and_faq import ConversationShare
    
    # Setup database records for a shared conversation
    session = get_session()
    try:
        # Create a test user or find one
        user = session.exec(select(User)).first()
        if not user:
            user = User(email="shared_owner@example.com", hashed_password="hashedpassword")
            session.add(user)
            session.commit()
            session.refresh(user)
            
        conv = Conversation(
            user_id=user.id,
            title="Shared Conversation Title",
            is_shared=True
        )
        session.add(conv)
        session.commit()
        session.refresh(conv)
        
        share = ConversationShare(
            conversation_id=conv.id,
            shared_by_user_id=user.id,
            share_token="xyz123_token"
        )
        session.add(share)
        session.commit()
        session.refresh(share)
        
        msg_user = Message(
            conversation_id=conv.id,
            role="user",
            content="Hello from test user"
        )
        msg_assistant = Message(
            conversation_id=conv.id,
            role="assistant",
            content="Hello from assistant"
        )
        session.add(msg_user)
        session.add(msg_assistant)
        session.commit()
        
        # Test endpoint
        response = client.get("/api/v1/tools/shared-conversation/xyz123_token")
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Shared Conversation Title"
        assert len(data["messages"]) == 2
        assert data["messages"][0]["role"] == "user"
        assert data["messages"][0]["content"] == "Hello from test user"
        assert data["messages"][1]["role"] == "assistant"
        assert data["messages"][1]["content"] == "Hello from assistant"
        
        # Cleanup
        session.delete(msg_assistant)
        session.delete(msg_user)
        session.delete(share)
        session.delete(conv)
        session.commit()
        
    finally:
        session.close()
