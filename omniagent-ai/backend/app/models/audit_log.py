from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field


class AuditLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[int] = Field(default=None, foreign_key="user.id")
    action: str
    entity: str
    entity_id: Optional[str] = None
    meta: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)