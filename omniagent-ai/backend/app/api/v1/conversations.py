from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlmodel import Session
from typing import List

from app.deps import db_session, current_user
from app.repositories.conversation_repo import ConversationRepo
from app.models.user import User
from app.schemas.common import PaginatedResponse

router = APIRouter()


class ConversationOut(BaseModel):
    id: int
    title: str
    user_id: int
    model: str
    created_at: str
    updated_at: str


@router.get("/", response_model=PaginatedResponse)
def list_conversations(
    db: Session = Depends(db_session),
    user: User = Depends(current_user),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    items, total = ConversationRepo(db).for_user(user.id, limit=limit, offset=offset)
    return PaginatedResponse(
        items=[{"id": c.id, "title": c.title, "model": c.model, "created_at": c.created_at.isoformat(), "updated_at": c.updated_at.isoformat()} for c in items],
        total=total,
        limit=limit,
        offset=offset
    )


@router.get("/search")
def search_conversations(
    db: Session = Depends(db_session),
    user: User = Depends(current_user),
    q: str = Query("", min_length=1, max_length=100, description="Search query")
):
    """Search conversations by title (case-insensitive)"""
    repo = ConversationRepo(db)
    results = repo.search(user.id, q)
    return {"results": [{"id": c.id, "title": c.title, "model": c.model, "created_at": c.created_at.isoformat()} for c in results[:20]]}


@router.get("/{conv_id}")
def get_conversation(conv_id: int, db: Session = Depends(db_session), user: User = Depends(current_user)):
    """Get a specific conversation with all metadata"""
    repo = ConversationRepo(db)
    conv = repo.get(conv_id)
    if not conv or conv.user_id != user.id:
        raise HTTPException(status_code=404, detail="Conversation not found")
    messages = repo.messages(conv_id)
    return {
        "id": conv.id,
        "title": conv.title,
        "model": conv.model,
        "created_at": conv.created_at.isoformat(),
        "updated_at": conv.updated_at.isoformat(),
        "message_count": len(messages)
    }


@router.get("/{conv_id}/messages")
def list_messages(conv_id: int, db: Session = Depends(db_session), user: User = Depends(current_user)):
    repo = ConversationRepo(db)
    conv = repo.get(conv_id)
    if not conv or conv.user_id != user.id:
        raise HTTPException(status_code=404, detail="Not found")
    return repo.messages(conv_id)


@router.delete("/{conv_id}")
def delete_conversation(conv_id: int, db: Session = Depends(db_session), user: User = Depends(current_user)):
    """Delete a conversation and all its messages"""
    repo = ConversationRepo(db)
    conv = repo.get(conv_id)
    if not conv or conv.user_id != user.id:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Delete all messages first
    repo.delete_messages(conv_id)
    # Then delete conversation
    repo.delete(conv_id)
    return {"status": "deleted", "id": conv_id}