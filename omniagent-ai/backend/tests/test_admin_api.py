
import pytest
from fastapi.testclient import TestClient
from app.models.user import User
from app.deps import current_user

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

def test_admin_dashboard_access(client: TestClient, mock_admin):
    from app.main import app
    app.dependency_overrides[current_user] = mock_admin
    response = client.get("/api/v1/admin/dashboard")
    assert response.status_code == 200
    data = response.json()
    assert "overview" in data
    app.dependency_overrides.clear()

def test_admin_dashboard_denied_for_regular_user(client: TestClient, mock_user):
    from app.main import app
    app.dependency_overrides[current_user] = mock_user
    response = client.get("/api/v1/admin/dashboard")
    # Admin dashboard requires is_admin check which might be inside the route or a decorator
    # If it's a decorator on the router, it might return 403 or 401
    assert response.status_code in [403, 401]
    app.dependency_overrides.clear()
