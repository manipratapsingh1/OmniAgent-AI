from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import jwt, JWTError

# --- Monkeypatch bcrypt 5.x / passlib 1.7.4 compatibility ---
# bcrypt 5.0+ raises ValueError for passwords > 72 bytes instead of silently
# truncating.  passlib 1.7.4 (unmaintained) triggers this during its internal
# detect_wrap_bug() initialization check with a 256-byte test string.
# We patch both bcrypt functions AND passlib's bug-detection to avoid the crash.
import bcrypt as _bcrypt_mod

_original_hashpw = _bcrypt_mod.hashpw
_original_checkpw = _bcrypt_mod.checkpw

def _safe_hashpw(password, salt):
    if isinstance(password, bytes) and len(password) > 72:
        password = password[:72]
    return _original_hashpw(password, salt)

def _safe_checkpw(password, hashed_password):
    if isinstance(password, bytes) and len(password) > 72:
        password = password[:72]
    return _original_checkpw(password, hashed_password)

_bcrypt_mod.hashpw = _safe_hashpw
_bcrypt_mod.checkpw = _safe_checkpw

# Patch passlib's detect_wrap_bug before it ever runs
import passlib.handlers.bcrypt as _passlib_bcrypt_handler
_passlib_bcrypt_handler.detect_wrap_bug = lambda *args, **kwargs: False

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