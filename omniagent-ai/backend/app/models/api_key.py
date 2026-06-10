from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field


class APIKey(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(index=True, foreign_key="user.id")
    key_hash: str = Field(unique=True, index=True)
    name: str
    is_active: bool = True
    last_used: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
