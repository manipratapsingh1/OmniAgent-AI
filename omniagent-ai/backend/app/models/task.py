from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field


class Task(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(index=True, foreign_key="user.id")
    title: str
    description: Optional[str] = None
    status: str = "pending"  # pending|in_progress|done|failed
    priority: int = 3
    tags: Optional[str] = None  # Comma-separated tags
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)