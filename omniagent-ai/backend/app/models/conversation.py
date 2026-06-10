from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field


class Conversation(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(index=True, foreign_key="user.id")
    title: str = "New Conversation"
    model: str = "llama3.2"
    is_pinned: bool = Field(default=False)
    is_shared: bool = Field(default=False)
    folder_name: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

