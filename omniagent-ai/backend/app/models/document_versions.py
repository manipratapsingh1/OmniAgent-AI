"""Document versioning and history tracking."""

from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field


class DocumentVersion(SQLModel, table=True):
    """Version history for documents."""
    id: Optional[int] = Field(default=None, primary_key=True)
    document_id: int = Field(index=True, foreign_key="document.id", ondelete="CASCADE")
    version_number: int  # 1, 2, 3...
    filename: str
    size_bytes: int
    chunk_count: int
    indexed_at: datetime
    notes: Optional[str] = None  # Version release notes
    created_at: datetime = Field(default_factory=datetime.utcnow)


class DocumentSummary(SQLModel, table=True):
    """Auto-generated document summaries."""
    id: Optional[int] = Field(default=None, primary_key=True)
    document_id: int = Field(unique=True, index=True, foreign_key="document.id", ondelete="CASCADE")
    summary: str  # Generated summary text
    key_points: str  # JSON array of key points
    generated_at: datetime = Field(default_factory=datetime.utcnow)
