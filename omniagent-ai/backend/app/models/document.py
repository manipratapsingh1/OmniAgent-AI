from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field


class Document(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(index=True, foreign_key="user.id")
    filename: str
    mime_type: str
    size_bytes: int
    status: str = "pending"  # pending | indexed | failed
    embedding_status: str = "pending"  # pending | embedded | failed
    chunk_count: int = 0  # Count of chunks for this document
    error_message: Optional[str] = None  # Error details if status="failed"
    last_indexed_at: Optional[datetime] = None  # When embeddings were created
    vector_ids_prefix: str = ""  # Prefix for vector IDs in Chroma (e.g., "doc-123-")
    is_knowledge_base: bool = False  # If True, admin-uploaded doc for knowledge base; if False, user-uploaded doc
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class DocumentChunk(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    document_id: int = Field(index=True, foreign_key="document.id", ondelete="CASCADE")
    chunk_index: int
    text: str
    vector_id: str = ""  # Chroma vector ID (now required and populated)