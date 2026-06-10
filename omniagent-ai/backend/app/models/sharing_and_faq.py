"""Conversation sharing and FAQ models."""

from datetime import datetime, timedelta
from typing import Optional
from sqlmodel import SQLModel, Field


class ConversationShare(SQLModel, table=True):
    """Share conversations with other users."""
    id: Optional[int] = Field(default=None, primary_key=True)
    conversation_id: int = Field(index=True, foreign_key="conversation.id", ondelete="CASCADE")
    shared_by_user_id: int = Field(foreign_key="user.id")
    share_token: str = Field(unique=True, index=True)  # Unique token for sharing
    shared_with_user_id: Optional[int] = Field(foreign_key="user.id")  # Specific user or null=public
    expires_at: Optional[datetime] = None  # Auto-expiry
    access_count: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)


class FrequentlyAskedQuestion(SQLModel, table=True):
    """Auto-generated FAQs from documents."""
    id: Optional[int] = Field(default=None, primary_key=True)
    document_id: int = Field(index=True, foreign_key="document.id", ondelete="CASCADE")
    question: str
    answer: str
    relevance_score: float = 0.8  # 0-1
    frequency_rank: int = 1  # How common this question is
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class QueryTemplate(SQLModel, table=True):
    """Pre-built query templates for common questions."""
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str  # "What is our policy on X?"
    template: str  # Parameterized query
    category: str  # "HR", "Finance", "General"
    icon: Optional[str] = None
    usage_count: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
