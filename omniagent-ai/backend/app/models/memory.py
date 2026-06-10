from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, JSON
from sqlmodel import SQLModel, Field


class MemoryEntry(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(index=True, foreign_key="user.id")
    memory_type: str = Field(default="short_term", index=True)  # short_term, long_term
    content: str
    embedding: Optional[List[float]] = Field(default=None, sa_column=Column(JSON))
    ttl: Optional[int] = None  # time to live in seconds
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None

class LearnedFact(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(index=True, foreign_key="user.id")
    fact: str
    category: Optional[str] = "preference" # preference, bio, work, etc.
    confidence: float = 1.0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
