from datetime import datetime
from typing import Optional, List

from sqlalchemy import Column, JSON
from sqlmodel import SQLModel, Field


class Response(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    conversation_id: int = Field(index=True, foreign_key="conversation.id")
    user_id: int = Field(index=True, foreign_key="user.id")

    content: str
    rating: Optional[int] = None  # 1-5 or thumbs up/down
    helpful: Optional[bool] = None  # True/False for thumbs

    # Store list safely as JSON in DB
    citations: List[str] = Field(default_factory=list, sa_column=Column(JSON))

    reasoning_trace: Optional[str] = None  # for transparency
    created_at: datetime = Field(default_factory=datetime.utcnow)