from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field


class Message(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    conversation_id: int = Field(index=True, foreign_key="conversation.id")
    role: str  # user | assistant | system | tool
    content: str
    agent: Optional[str] = None
    sources: Optional[str] = None  # JSON string of citations
    created_at: datetime = Field(default_factory=datetime.utcnow)