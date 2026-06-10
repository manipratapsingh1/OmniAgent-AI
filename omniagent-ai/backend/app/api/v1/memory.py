from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session
from pydantic import BaseModel
from typing import List, Optional

from app.config import get_settings
from app.deps import db_session, current_user
from app.models.user import User
from app.repositories.conversation_repo import ConversationRepo
from app.services.ai.service import AIService
from app.services.memory_service import MemoryService
from app.rag.embeddings import embed_texts

router = APIRouter()


class MemoryEntryResponse(BaseModel):
    id: int
    memory_type: str
    content: str
    created_at: str

    class Config:
        from_attributes = True


class MemoryStore(BaseModel):
    content: str
    memory_type: str = "short_term"  # or long_term
    ttl: Optional[int] = 3600


class MemorySummarizeRequest(BaseModel):
    conversation_id: int
    memory_type: str = "long_term"
    ttl: Optional[int] = 3600
    model: Optional[str] = None
    system_prompt: Optional[str] = None


@router.post("/memory/summarize")
async def summarize_conversation(
    req: MemorySummarizeRequest,
    db: Session = Depends(db_session),
    user: User = Depends(current_user),
):
    settings = get_settings()
    memory_service = MemoryService(db)
    conversation_repo = ConversationRepo(db)

    conversation = conversation_repo.get(req.conversation_id)
    if not conversation or conversation.user_id != user.id:
        raise HTTPException(status_code=404, detail="Conversation not found")

    messages = conversation_repo.messages(req.conversation_id)
    if not messages:
        raise HTTPException(status_code=404, detail="Conversation has no messages to summarize")

    transcript = "\n".join(
        [f"{msg.role.title()}: {msg.content}" for msg in messages[-30:]]
    )

    prompt = (
        "Summarize the following conversation into a concise memory entry for later recall. "
        "Capture the key topics, decisions, and user preferences, and keep it under 300 words.\n\n"
        f"Conversation:\n{transcript}"
    )

    ai_service = AIService(db=db, provider="ollama")
    summary_text = await ai_service.generate(
        prompt=prompt,
        model=req.model or settings.OLLAMA_DEFAULT_MODEL,
        system=req.system_prompt,
    )

    saved_entry = None
    if req.memory_type == "short_term":
        saved_entry = memory_service.store_short_term(user.id, summary_text, ttl=req.ttl or settings.SHORT_TERM_MEMORY_TTL)
    else:
        embeddings = await embed_texts([summary_text])
        saved_entry = memory_service.store_long_term(
            user.id,
            summary_text,
            embedding=embeddings[0] if embeddings else None,
        )

    return MemoryEntryResponse(
        id=saved_entry.id,
        memory_type=saved_entry.memory_type,
        content=saved_entry.content,
        created_at=saved_entry.created_at.isoformat(),
    )


@router.post("/memory")
def store_memory(
    req: MemoryStore,
    db: Session = Depends(db_session),
    user: User = Depends(current_user)
):
    """Store memory entry"""
    service = MemoryService(db)
    
    if req.memory_type == "short_term":
        entry = service.store_short_term(user.id, req.content, req.ttl or 3600)
    else:
        entry = service.store_long_term(user.id, req.content)
    
    return MemoryEntryResponse(
        id=entry.id,
        memory_type=entry.memory_type,
        content=entry.content,
        created_at=entry.created_at.isoformat()
    )


@router.get("/memory/short-term", response_model=List[MemoryEntryResponse])
def get_short_term_memory(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(db_session),
    user: User = Depends(current_user)
):
    """Get short-term memory entries"""
    service = MemoryService(db)
    entries = service.get_short_term(user.id, limit)
    
    return [
        MemoryEntryResponse(
            id=e.id,
            memory_type=e.memory_type,
            content=e.content,
            created_at=e.created_at.isoformat()
        )
        for e in entries
    ]


@router.get("/memory/long-term", response_model=List[MemoryEntryResponse])
def get_long_term_memory(
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(db_session),
    user: User = Depends(current_user)
):
    """Get long-term memory entries"""
    service = MemoryService(db)
    entries = service.get_long_term(user.id, limit)
    
    return [
        MemoryEntryResponse(
            id=e.id,
            memory_type=e.memory_type,
            content=e.content,
            created_at=e.created_at.isoformat()
        )
        for e in entries
    ]


@router.get("/memory/search", response_model=List[MemoryEntryResponse])
def search_memory(
    q: str = Query(..., min_length=1),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(db_session),
    user: User = Depends(current_user)
):
    """Search memory entries"""
    service = MemoryService(db)
    entries = service.search_memories(user.id, q, limit)
    
    return [
        MemoryEntryResponse(
            id=e.id,
            memory_type=e.memory_type,
            content=e.content,
            created_at=e.created_at.isoformat()
        )
        for e in entries
    ]
