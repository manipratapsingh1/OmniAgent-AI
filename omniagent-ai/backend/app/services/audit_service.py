import structlog
from typing import Optional, Any
from sqlmodel import Session
from app.models.audit_log import AuditLog
from datetime import datetime, timezone

log = structlog.get_logger("audit")

class AuditService:
    def __init__(self, db: Session):
        self.db = db

    def log(self, action: str, entity: str, user_id: Optional[int] = None, entity_id: Optional[str] = None, meta: Optional[Any] = None):
        """Create a new audit log entry."""
        import json
        meta_str = json.dumps(meta) if meta else None
        
        entry = AuditLog(
            user_id=user_id,
            action=action,
            entity=entity,
            entity_id=entity_id,
            meta=meta_str,
            created_at=datetime.now(timezone.utc)
        )
        self.db.add(entry)
        self.db.commit()
        log.info("audit.logged", action=action, entity=entity, user_id=user_id)
        return entry
