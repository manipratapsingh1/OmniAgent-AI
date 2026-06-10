from sqlmodel import SQLModel, Field
from typing import Optional
import datetime


class ToolLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int
    tool_name: str
    args: Optional[str] = None
    result: Optional[str] = None
    success: bool = Field(default=True)
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)
