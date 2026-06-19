from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from pydantic import BaseModel, ConfigDict
from typing import List, Optional

from app.deps import db_session, current_user
from app.models.user import User
from app.services.api_key_service import APIKeyService
import structlog

log = structlog.get_logger("api_keys")

router = APIRouter()


class APIKeyCreate(BaseModel):
    name: str
    expires_in_days: Optional[int] = 365


class APIKeyResponse(BaseModel):
    id: int
    name: str
    key_preview: str  # First 10 chars + last 4 chars
    is_active: bool
    created_at: str
    expires_at: Optional[str]
    last_used: Optional[str]

    model_config = ConfigDict(from_attributes=True)


class APIKeyCreateResponse(APIKeyResponse):
    key: str  # Only shown once


@router.post("/keys", response_model=APIKeyCreateResponse)
def create_api_key(
    req: APIKeyCreate,
    db: Session = Depends(db_session),
    user: User = Depends(current_user)
):
    """Create new API key for current user"""
    service = APIKeyService(db)
    raw_key, api_key = service.create_key(user.id, req.name, req.expires_in_days)
    
    key_preview = f"{raw_key[:10]}...{raw_key[-4:]}"
    
    return APIKeyCreateResponse(
        id=api_key.id,
        name=api_key.name,
        key=raw_key,
        key_preview=key_preview,
        is_active=api_key.is_active,
        created_at=api_key.created_at.isoformat(),
        expires_at=api_key.expires_at.isoformat() if api_key.expires_at else None,
        last_used=api_key.last_used.isoformat() if api_key.last_used else None
    )


@router.get("/keys", response_model=List[APIKeyResponse])
def list_api_keys(
    db: Session = Depends(db_session),
    user: User = Depends(current_user)
):
    """List all API keys for current user"""
    service = APIKeyService(db)
    keys = service.list_keys(user.id)
    
    result = []
    for key in keys:
        key_preview = f"{key.key_hash[:10]}...{key.key_hash[-4:]}"
        result.append(APIKeyResponse(
            id=key.id,
            name=key.name,
            key_preview=key_preview,
            is_active=key.is_active,
            created_at=key.created_at.isoformat(),
            expires_at=key.expires_at.isoformat() if key.expires_at else None,
            last_used=key.last_used.isoformat() if key.last_used else None
        ))
    
    return result


@router.delete("/keys/{key_id}")
def revoke_api_key(
    key_id: int,
    db: Session = Depends(db_session),
    user: User = Depends(current_user)
):
    """Revoke an API key"""
    service = APIKeyService(db)
    success = service.revoke_key(user.id, key_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="API key not found")
    
    return {"status": "revoked"}
