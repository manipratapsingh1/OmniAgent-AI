from fastapi import APIRouter, Depends, Query
from sqlmodel import Session
from pydantic import BaseModel, ConfigDict
from typing import List, Optional

from app.deps import db_session, current_user
from app.models.user import User
from app.services.search_service import SearchService

router = APIRouter()


class ConversationSummary(BaseModel):
    id: int
    title: str
    updated_at: str

    model_config = ConfigDict(from_attributes=True)


class MessageResult(BaseModel):
    id: int
    content: str
    created_at: str

    model_config = ConfigDict(from_attributes=True)


@router.get("/search/conversations", response_model=List[ConversationSummary])
def search_conversations(
    q: str = Query(..., min_length=1, max_length=100),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(db_session),
    user: User = Depends(current_user)
):
    """Search conversations by title"""
    service = SearchService(db)
    convs = service.search_conversations(user.id, q, limit)
    
    return [
        ConversationSummary(
            id=c.id,
            title=c.title,
            updated_at=c.updated_at.isoformat()
        )
        for c in convs
    ]


@router.get("/search/messages", response_model=List[MessageResult])
def search_messages(
    q: str = Query(..., min_length=1, max_length=100),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(db_session),
    user: User = Depends(current_user)
):
    """Search messages by content"""
    service = SearchService(db)
    messages = service.search_messages(user.id, q, limit)
    
    return [
        MessageResult(
            id=m.id,
            content=m.content,
            created_at=m.created_at.isoformat()
        )
        for m in messages
    ]
