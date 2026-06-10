from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field


class AgentRun(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    conversation_id: int = Field(index=True, foreign_key="conversation.id")
    agent: str
    input: str
    output: str
    success: bool = True
    latency_ms: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)