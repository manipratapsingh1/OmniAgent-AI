from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field


class Notification(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(index=True, foreign_key="user.id")
    notification_type: str  # task_update, upload_complete, agent_alert, system
    title: str
    message: str
    data: Optional[str] = None  # JSON payload
    is_read: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
