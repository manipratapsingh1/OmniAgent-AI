def test_health(client):
    assert client.get("/healthz").status_code == 200