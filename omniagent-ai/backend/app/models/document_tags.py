"""Document tagging and categorization models."""

from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field


class DocumentTag(SQLModel, table=True):
    """Tags for organizing documents."""
    id: Optional[int] = Field(default=None, primary_key=True)
    document_id: int = Field(index=True, foreign_key="document.id", ondelete="CASCADE")
    tag: str = Field(index=True)  # e.g., "payroll", "benefits", "hr"
    category: Optional[str] = None  # e.g., "HR", "Engineering", "Finance"
    created_at: datetime = Field(default_factory=datetime.utcnow)


class DocumentCategory(SQLModel, table=True):
    """Document categories/classifications."""
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True)  # HR, Engineering, Finance, etc.
    description: Optional[str] = None
    color: Optional[str] = None  # Hex color for UI
    icon: Optional[str] = None  # Icon name
    created_at: datetime = Field(default_factory=datetime.utcnow)
