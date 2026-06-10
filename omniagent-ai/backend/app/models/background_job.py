from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field


class BackgroundJob(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(index=True, foreign_key="user.id")
    job_type: str  # embedding, upload, indexing, analysis
    status: str = "pending"  # pending, processing, completed, failed
    task_id: Optional[str] = None  # Celery task ID
    result: Optional[str] = None  # JSON result
    error: Optional[str] = None
    progress: int = 0  # 0-100
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
