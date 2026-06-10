from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class DocumentOut(BaseModel):
    id: int
    filename: str
    mime_type: str
    size_bytes: int
    status: str
    embedding_status: str
    chunk_count: int
    error_message: Optional[str] = None
    last_indexed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime