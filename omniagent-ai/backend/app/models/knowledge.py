from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import Column, JSON
from sqlmodel import SQLModel, Field


class KnowledgeRelationship(SQLModel, table=True):
    """Stores semantic relationships between entities (Graph Memory)."""
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(index=True, foreign_key="user.id")
    source_id: str = Field(index=True) # e.g. "doc:123", "topic:AI"
    source_type: str # e.g. "document", "topic", "user"
    relation: str # e.g. "discusses", "belongs_to", "is_expert_in"
    target_id: str = Field(index=True)
    target_type: str
    weight: float = 1.0
    extra_data: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)


class StudyMaterial(SQLModel, table=True):
    """AI Second Brain: Stores generated flashcards, quizzes, and action items."""
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(index=True, foreign_key="user.id")
    document_id: Optional[int] = Field(default=None, foreign_key="document.id")
    material_type: str = Field(index=True) # "flashcard", "quiz", "action_item"
    content: Dict[str, Any] = Field(sa_column=Column(JSON)) # {question: "", answer: ""} or {task: ""}
    is_completed: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
