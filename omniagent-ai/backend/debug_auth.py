import os
os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")
os.environ.setdefault("SECRET_KEY", "x" * 40)
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/15")

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)
print('SIGNUP')
resp = client.post('/api/v1/auth/signup', json={'email':'a@b.com','password':'password123'})
print(resp.status_code)
try:
    print(resp.json())
except Exception as e:
    print('no json', e)
print('text:', repr(resp.text))
print('LOGIN')
resp2 = client.post('/api/v1/auth/login', json={'email':'a@b.com','password':'password123'})
print(resp2.status_code)
try:
    print(resp2.json())
except Exception as e:
    print('no json', e)
print('text:', repr(resp2.text))
