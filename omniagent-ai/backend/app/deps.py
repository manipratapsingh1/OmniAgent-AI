from typing import Generator, Optional

from fastapi import Depends, HTTPException, status, Header
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session, select

from app.core.security import decode_token
from app.db.session import get_session
from app.models.user import User
import structlog

log = structlog.get_logger("deps")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def db_session() -> Generator[Session, None, None]:
    """Get a database session as a dependency"""
    session = get_session()
    try:
        yield session
    except Exception as e:
        log.error("db_session.error", error=str(e))
        raise
    finally:
        session.close()


def current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(db_session),
) -> User:
    try:
        payload = decode_token(token)
        email: Optional[str] = payload.get("sub")
        if not email:
            raise ValueError("missing sub")
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

    user = db.exec(select(User).where(User.email == email)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    if not getattr(user, "is_active", True):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User inactive",
        )

    return user


def require_admin(user: User = Depends(current_user)) -> User:
    is_admin = getattr(user, "is_admin", False)
    role = getattr(user, "role", None)

    if not is_admin and role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin only",
        )

    return user


async def verify_api_key(
    x_api_key: Optional[str] = Header(None),
    db: Session = Depends(db_session),
) -> User:
    """Verify API key and return associated user"""
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key",
        )
    
    from app.services.api_key_service import APIKeyService
    service = APIKeyService(db)
    
    valid, api_key = service.verify_key(x_api_key)
    if not valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )
    
    user = db.exec(select(User).where(User.id == api_key.user_id)).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User inactive or not found",
        )
    
    return user