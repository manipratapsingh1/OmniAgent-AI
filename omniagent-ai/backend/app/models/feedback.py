from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field


class Feedback(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    message_id: int = Field(foreign_key="message.id")
    rating: int  # -1 | 0 | 1
    comment: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)