import secrets
import hashlib
from datetime import datetime, timedelta
from sqlmodel import Session, select
from app.models.api_key import APIKey
from typing import Tuple, Optional
import structlog

log = structlog.get_logger("api_keys")


class APIKeyService:
    def __init__(self, db: Session):
        self.db = db

    def create_key(self, user_id: int, name: str, expires_in_days: int = 365) -> Tuple[str, APIKey]:
        """Generate new API key"""
        raw_key = secrets.token_urlsafe(32)
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        
        expires_at = datetime.utcnow() + timedelta(days=expires_in_days) if expires_in_days else None
        
        api_key = APIKey(
            user_id=user_id,
            key_hash=key_hash,
            name=name,
            expires_at=expires_at
        )
        self.db.add(api_key)
        self.db.commit()
        self.db.refresh(api_key)
        
        log.info("api_key.created", user_id=user_id, name=name, key_id=api_key.id)
        return raw_key, api_key

    def verify_key(self, raw_key: str) -> Tuple[bool, Optional[APIKey]]:
        """Verify API key and return user"""
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        key_obj = self.db.exec(
            select(APIKey).where(
                APIKey.key_hash == key_hash,
                APIKey.is_active == True
            )
        ).first()
        
        if not key_obj:
            return False, None
        
        if key_obj.expires_at and key_obj.expires_at < datetime.utcnow():
            return False, None
        
        # Update last used
        key_obj.last_used = datetime.utcnow()
        self.db.add(key_obj)
        self.db.commit()
        
        return True, key_obj

    def list_keys(self, user_id: int):
        """List all keys for user (without showing full key)"""
        keys = self.db.exec(
            select(APIKey).where(APIKey.user_id == user_id)
        ).all()
        return keys

    def revoke_key(self, user_id: int, key_id: int) -> bool:
        """Revoke an API key"""
        key_obj = self.db.exec(
            select(APIKey).where(
                APIKey.id == key_id,
                APIKey.user_id == user_id
            )
        ).first()
        
        if not key_obj:
            return False
        
        key_obj.is_active = False
        self.db.add(key_obj)
        self.db.commit()
        
        log.info("api_key.revoked", user_id=user_id, key_id=key_id)
        return True
