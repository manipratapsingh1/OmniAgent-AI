from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field


class ToolCall(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    conversation_id: int = Field(index=True, foreign_key="conversation.id")
    tool: str
    arguments: str
    result: str
    success: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)