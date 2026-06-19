import os
os.environ["DATABASE_URL"] = "sqlite:///./test.db"
os.environ["SECRET_KEY"] = "x" * 40
os.environ["REDIS_URL"] = "redis://localhost:6379/15"
os.environ["ENABLE_WEB_SEARCH"] = "false"
os.environ["RATE_LIMIT_PER_MINUTE"] = "100000"

import sys
import uuid
from unittest.mock import MagicMock, patch

# Mock packages that might not be installed in the test runner environment
for module_name in ["openai", "pptx", "psutil"]:
    if module_name not in sys.modules:
        sys.modules[module_name] = MagicMock()

if "pandas" not in sys.modules:
    mock_pd = MagicMock()
    mock_pd.read_csv.return_value.to_string.return_value = "name,age\nAlice,30\nBob,25"
    mock_pd.read_excel.return_value = {}
    sys.modules["pandas"] = mock_pd

# Mock chromadb to avoid network connections during test initialization
try:
    import chromadb
    chromadb.HttpClient = MagicMock()
except Exception:
    pass

# Mock OllamaClient to avoid blocking network calls during tests
try:
    from app.llm.ollama_client import ollama
    from unittest.mock import AsyncMock
    ollama.generate = AsyncMock(return_value="Ollama test response")
    ollama.list_models = AsyncMock(return_value=["phi3:mini"])
    
    async def mock_embed(texts, model=None):
        return [[0.1] * 768 for _ in texts]
    ollama.embed = mock_embed

    async def mock_stream(prompt, model=None, system=None, images=None):
        yield "Ollama"
        yield " "
        yield "response"
    ollama.stream = mock_stream
except Exception:
    pass


import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session
from app.main import app
from app.models.user import User
from app.core.security import hash_password
from unittest.mock import MagicMock


@pytest.fixture
def db_session_mock():
    mock = MagicMock(spec=Session)
    return mock


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def admin_user():
    user = User(
        email="admin_test@example.com",
        hashed_password=hash_password("admin123"),
        is_admin=True,
        full_name="Admin Test",
    )
    return user


@pytest.fixture
def normal_user():
    user = User(
        email="user_test@example.com",
        hashed_password=hash_password("user123"),
        is_admin=False,
        full_name="User Test",
    )
    return user


@pytest.fixture
def unique_email():
    return f"test_{uuid.uuid4().hex[:8]}@example.com"


@pytest.fixture
def auth_headers(client, unique_email):
    """Register a user and return Authorization headers."""
    password = "securepass123"
    client.post(
        "/api/v1/auth/signup",
        json={"email": unique_email, "password": password, "full_name": "Test User"},
    )
    r = client.post(
        "/api/v1/auth/login",
        json={"email": unique_email, "password": password},
    )
    assert r.status_code == 200, r.text
    token = r.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}