from typing import List, Optional, Literal
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    conversation_id: Optional[int] = None
    message: str = Field(min_length=1, max_length=10000, description="Chat message content")
    model: Optional[str] = Field(None, max_length=256)
    use_rag: bool = True
    force_fresh: bool = Field(False, description="Force fresh response, bypass cache")
    system_prompt: Optional[str] = Field(None, max_length=1000, description="Optional custom system prompt or persona for the assistant")
    images: List[str] = Field(default=[], description="List of base64 encoded images for vision support")
    knowledge_mode: Optional[Literal["auto", "documents_only", "ai_only"]] = Field(
        "auto",
        description="Knowledge routing mode: auto (hybrid), documents_only, or ai_only",
    )


class Citation(BaseModel):
    document_id: int
    chunk_index: int
    snippet: str
    document_name: Optional[str] = None
    page_number: Optional[int] = None
    section: Optional[str] = None
    confidence_score: Optional[float] = None


class AgentTrace(BaseModel):
    agent: str
    input: str
    output: str
    latency_ms: int


class ChatResponse(BaseModel):
    conversation_id: int
    message_id: int
    content: str
    sources: List[Citation] = []
    trace: List[AgentTrace] = []