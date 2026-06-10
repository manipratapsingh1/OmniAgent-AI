import os
os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")
os.environ.setdefault("SECRET_KEY", "x" * 40)
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/15")

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from app.main import app
from app.db.session import engine
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
        full_name="Admin Test"
    )
    return user

@pytest.fixture
def normal_user():
    user = User(
        email="user_test@example.com",
        hashed_password=hash_password("user123"),
        is_admin=False,
        full_name="User Test"
    )
    return user