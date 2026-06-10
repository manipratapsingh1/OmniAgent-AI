import os
os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")
os.environ.setdefault("SECRET_KEY", "x" * 40)
from app.core.security import hash_password
print(hash_password('password123'))
