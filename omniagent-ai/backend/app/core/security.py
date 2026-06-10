from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import jwt, JWTError
from passlib.context import CryptContext

from app.config import get_settings

# Use pbkdf2_sha256 to avoid optional native bcrypt backend issues in some
# environments (works cross-platform and during CI/tests)
_pwd = CryptContext(
    schemes=["bcrypt", "pbkdf2_sha256"],
    deprecated="auto"
)
_settings = get_settings()


def hash_password(password: str) -> str:
    return _pwd.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return _pwd.verify(plain, hashed)


def create_access_token(subject: str, extra: Optional[dict] = None) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=_settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": subject, "exp": expire, "type": "access", **(extra or {})}
    return jwt.encode(payload, _settings.SECRET_KEY, algorithm=_settings.JWT_ALGORITHM)


def create_refresh_token(subject: str, extra: Optional[dict] = None) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=_settings.REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {"sub": subject, "exp": expire, "type": "refresh", **(extra or {})}
    return jwt.encode(payload, _settings.SECRET_KEY, algorithm=_settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, _settings.SECRET_KEY, algorithms=[_settings.JWT_ALGORITHM])
    except JWTError as e:
        raise ValueError("Invalid token") from e