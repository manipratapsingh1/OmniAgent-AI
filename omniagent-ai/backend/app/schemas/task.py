from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=512, description="Task title")
    description: Optional[str] = Field(None, max_length=4000)
    priority: int = Field(3, ge=1, le=5, description="Priority level 1-5")
    tags: Optional[List[str]] = Field(None, description="Task tags for categorization")


class TaskOut(BaseModel):
    id: int
    title: str
    description: Optional[str]
    status: str
    priority: int
    tags: Optional[str]
    created_at: datetime