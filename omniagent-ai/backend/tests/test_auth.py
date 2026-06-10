def test_signup_and_login(client):
    r = client.post("/api/v1/auth/signup", json={"email": "a@b.com", "password": "password123"})
    assert r.status_code in (200, 400)
    r = client.post("/api/v1/auth/login", json={"email": "a@b.com", "password": "password123"})
    assert r.status_code == 200
    assert "access_token" in r.json()