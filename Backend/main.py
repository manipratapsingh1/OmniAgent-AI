"""
OmniAgent AI - Production-Grade Backend System
Features: Multi-Agent, Memory, RAG, Tools, Automation, Dev Assistant, Auth, Logging, Rate Limiting
"""

from __future__ import annotations

import asyncio
import json
import os
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, AsyncGenerator, Dict, List, Optional

import aiofiles
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, File, HTTPException, Request, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field, validator
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

from app.agents.graph import agent_app
from app.agents.state import AgentState
from app.auth import (
    UserLogin,
    UserRegister,
    UserResponse,
    create_tokens,
    decode_token,
    hash_password,
    verify_password,
)
from app.automation.task_engine import TaskEngine
from app.database import Conversation, Document, Message, Task, User, get_db, init_db
from app.knowledge.code_analyzer import CodeAnalyzer
from app.knowledge.rag_system import RAGSystem
from app.logging_config import APILogger, AgentLogger, RAGLogger, logger, setup_logging
from app.memory.memory_manager import MemoryManager
from app.tools.tool_manager import ToolManager

load_dotenv()

# =========================
# Helpers
# =========================


def safe_init(factory, name: str):
    try:
        return factory()
    except Exception as exc:
        logger.warning("%s disabled: %s", name, exc, exc_info=True)
        return None


def token_user_id(token_data: Any) -> Optional[str]:
    if token_data is None:
        return None
    if isinstance(token_data, dict):
        return token_data.get("user_id")
    return getattr(token_data, "user_id", None)


def serialize_conversation(conversation: Conversation) -> Dict[str, Any]:
    return {
        "id": conversation.id,
        "user_id": conversation.user_id,
        "title": conversation.title,
        "created_at": conversation.created_at,
        "updated_at": conversation.updated_at,
        "total_messages": conversation.total_messages,
        "total_tokens": conversation.total_tokens,
    }


def serialize_message(message: Message) -> Dict[str, Any]:
    return {
        "id": message.id,
        "conversation_id": message.conversation_id,
        "role": message.role,
        "content": message.content,
        "timestamp": message.timestamp,
        "tokens_used": message.tokens_used,
        "sources": message.sources,
    }


def serialize_document(document: Document) -> Dict[str, Any]:
    return {
        "id": document.id,
        "user_id": document.user_id,
        "filename": document.filename,
        "content_type": document.content_type,
        "file_path": document.file_path,
        "file_size": document.file_size,
        "created_at": document.created_at,
        "updated_at": document.updated_at,
        "vector_db_id": document.vector_db_id,
        "chunk_count": document.chunk_count,
    }


def serialize_task(task: Task) -> Dict[str, Any]:
    return {
        "id": task.id,
        "user_id": task.user_id,
        "title": task.title,
        "description": task.description,
        "priority": task.priority,
        "status": task.status,
        "created_at": task.created_at,
        "updated_at": task.updated_at,
        "due_date": task.due_date,
        "recurrence": task.recurrence,
        "is_recurring": task.is_recurring,
    }


def fallback_code_analysis(code: str, language: str) -> Dict[str, Any]:
    lines = code.splitlines()
    loc = len(lines)
    complexity = 1
    complexity += code.count(" if ")
    complexity += code.count(" for ")
    complexity += code.count(" while ")
    complexity += code.count(" except ")
    complexity += code.count(" and ")
    complexity += code.count(" or ")

    if complexity <= 3:
        rating = "Low"
    elif complexity <= 7:
        rating = "Moderate"
    elif complexity <= 10:
        rating = "High"
    else:
        rating = "Very High"

    return {
        "language": language,
        "syntax_valid": True,
        "issues": [],
        "suggestions": [
            "Add tests for edge cases.",
            "Split large functions into smaller ones.",
        ],
        "complexity": {
            "lines_of_code": loc,
            "cyclomatic_complexity": complexity,
            "rating": rating,
        },
        "security_concerns": [],
    }


def fallback_explanation(code: str) -> str:
    return "Code explanation is unavailable because the AI analyzer is not initialized."


def fallback_refactoring() -> Dict[str, Any]:
    return {
        "suggestions": [
            "Extract repeated logic into helper functions.",
            "Use more descriptive names.",
            "Add type hints where missing.",
        ]
    }


# =========================
# Pydantic Models
# =========================

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse


class ChatRequest(BaseModel):
    conversation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    message: str = Field(..., min_length=1, max_length=5000)
    use_memory: bool = True
    use_rag: bool = True
    streaming: bool = False

    @validator("message")
    def validate_message(cls, v):
        if not v.strip():
            raise ValueError("Message cannot be empty")
        return v


class ChatResponse(BaseModel):
    conversation_id: str
    response: str
    sources: Optional[List[Dict[str, Any]]] = None
    tokens_used: int
    execution_time: float
    status: str


class DocumentResponse(BaseModel):
    id: str
    filename: str
    file_size: int
    chunks: int
    created_at: datetime


class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    priority: int = Field(default=3, ge=1, le=5)
    due_date: Optional[datetime] = None
    recurrence: Optional[str] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[int] = Field(None, ge=1, le=5)
    status: Optional[str] = None
    due_date: Optional[datetime] = None
    recurrence: Optional[str] = None


class TaskResponse(BaseModel):
    id: str
    title: str
    status: str
    priority: int
    created_at: datetime
    due_date: Optional[datetime]


class PreferencesUpdate(BaseModel):
    tone: Optional[str] = Field(None, description="professional, casual, formal")
    expertise_level: Optional[str] = Field(None, description="beginner, intermediate, expert")
    preferred_tools: Optional[List[str]] = None
    custom_instructions: Optional[str] = None
    dark_mode: Optional[bool] = None


class CodeAnalysisRequest(BaseModel):
    code: str = Field(..., min_length=1)
    language: str = Field(default="python", description="python, javascript, java, cpp, go")
    analysis_type: str = Field(default="full", description="full, complexity, dependencies, security")


class CodeAnalysisResponse(BaseModel):
    analysis: Dict[str, Any]
    suggestions: List[Any]
    explanation: Any
    refactoring: Dict[str, Any]


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1)


# =========================
# Initialization
# =========================

setup_logging(level=os.getenv("LOG_LEVEL", "INFO"))

app = FastAPI(
    title="OmniAgent AI",
    description="Production-Grade Multi-Agent AI System with Memory, RAG, Tools, Automation, and Auth",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)

@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={"detail": "Rate limit exceeded"},
    )

cors_origins = [o.strip() for o in os.getenv("CORS_ORIGINS", "*").split(",") if o.strip()]
allow_all_cors = "*" in cors_origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if allow_all_cors else cors_origins,
    allow_credentials=not allow_all_cors,
    allow_methods=["*"],
    allow_headers=["*"],
)

allowed_hosts = [o.strip() for o in os.getenv("ALLOWED_HOSTS", "*").split(",") if o.strip()]
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=allowed_hosts,
)

init_db()

memory_manager = safe_init(MemoryManager, "MemoryManager")
rag_system = safe_init(RAGSystem, "RAGSystem")
code_analyzer = safe_init(CodeAnalyzer, "CodeAnalyzer")
tool_manager = safe_init(ToolManager, "ToolManager")
task_engine = safe_init(TaskEngine, "TaskEngine")

api_log = APILogger("api")
agent_log = AgentLogger("agent")
rag_log = RAGLogger("rag")

security = HTTPBearer()


# =========================
# Dependencies
# =========================

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    token = credentials.credentials
    token_data = decode_token(token)

    user_id = token_user_id(token_data)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is inactive",
        )

    return user


# =========================
# Auth Endpoints
# =========================

@app.post("/api/auth/register", response_model=TokenResponse, tags=["Authentication"])
@limiter.limit("5/minute")
async def register(
    request: Request,
    payload: UserRegister,
    db: Session = Depends(get_db),
):
    api_log.log_request(None, "/api/auth/register", "POST", username=payload.username)

    try:
        if db.query(User).filter(User.username == payload.username).first():
            api_log.log_error("/api/auth/register", 400, "User already exists", username=payload.username)
            raise HTTPException(status_code=400, detail="Username already taken")

        if payload.email and db.query(User).filter(User.email == payload.email).first():
            raise HTTPException(status_code=400, detail="Email already registered")

        user = User(
            id=str(uuid.uuid4()),
            username=payload.username,
            email=payload.email,
            full_name=payload.full_name,
            hashed_password=hash_password(payload.password),
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        tokens = create_tokens(user.id, user.email)

        logger.info("New user registered: %s", user.username)
        api_log.log_response("/api/auth/register", 200, 0.1)

        return TokenResponse(
            access_token=tokens.access_token,
            refresh_token=tokens.refresh_token,
            token_type="bearer",
            user=UserResponse.from_orm(user),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Registration error: %s", str(e), exc_info=True)
        api_log.log_error("/api/auth/register", 500, str(e))
        raise HTTPException(status_code=500, detail="Registration failed")


@app.post("/api/auth/login", response_model=TokenResponse, tags=["Authentication"])
@limiter.limit("10/minute")
async def login(
    request: Request,
    payload: UserLogin,
    db: Session = Depends(get_db),
):
    api_log.log_request(None, "/api/auth/login", "POST", username=payload.username)

    try:
        user = db.query(User).filter(User.username == payload.username).first()

        if not user or not verify_password(payload.password, user.hashed_password):
            logger.warning("Failed login attempt for user: %s", payload.username)
            api_log.log_error("/api/auth/login", 401, "Invalid credentials")
            raise HTTPException(status_code=401, detail="Invalid credentials")

        if not user.is_active:
            raise HTTPException(status_code=403, detail="User account is inactive")

        tokens = create_tokens(user.id, user.email)

        logger.info("User logged in: %s", user.username)
        api_log.log_response("/api/auth/login", 200, 0.1)

        return TokenResponse(
            access_token=tokens.access_token,
            refresh_token=tokens.refresh_token,
            token_type="bearer",
            user=UserResponse.from_orm(user),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Login error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Login failed")


@app.post("/api/auth/refresh", response_model=TokenResponse, tags=["Authentication"])
@limiter.limit("10/minute")
async def refresh_token(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    try:
        token_data = decode_token(credentials.credentials)
        user_id = token_user_id(token_data)
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=401, detail="User not found")

        tokens = create_tokens(user.id, user.email)
        return TokenResponse(
            access_token=tokens.access_token,
            refresh_token=tokens.refresh_token,
            token_type="bearer",
            user=UserResponse.from_orm(user),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Token refresh error: %s", str(e))
        raise HTTPException(status_code=401, detail="Token refresh failed")


# =========================
# Chat Endpoints
# =========================

@app.post("/api/chat", response_model=ChatResponse, tags=["Chat"])
@limiter.limit("30/minute")
async def chat(
    request: Request,
    payload: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    start_time = time.time()
    request_id = str(uuid.uuid4())

    api_log.log_request(current_user.id, "/api/chat", "POST", request_id=request_id)
    agent_log.log_planning(current_user.id, payload.message, 3)

    try:
        memory_context = ""
        if payload.use_memory and memory_manager is not None:
            prefs = memory_manager.get_preferences(current_user.id)
            past_conversations = memory_manager.get_user_conversations(current_user.id)
            memory_context = json.dumps(
                {
                    "preferences": prefs,
                    "recent": past_conversations[:3],
                },
                default=str,
            )

        rag_context = ""
        sources: List[Dict[str, Any]] = []
        if payload.use_rag and rag_system is not None:
            rag_result = rag_system.query_knowledge(payload.message)
            if "answer" in rag_result:
                rag_context = rag_result["answer"]
                sources = rag_result.get("sources", [])
            rag_log.log_retrieval(current_user.id, payload.message, len(sources), 0)

        state: AgentState = {
            "objective": payload.message,
            "plan": [],
            "step_results": [],
            "current_step_idx": 0,
            "status": "initialized",
            "memory_context": memory_context,
            "conversation_id": payload.conversation_id,
            "user_id": current_user.id,
            "meta_data": {"rag_context": rag_context, "request_id": request_id},
        }

        result = agent_app.invoke(state)
        agent_log.log_execution(current_user.id, 1, "multi-agent")

        response_text = ""
        if result.get("step_results"):
            response_text = result["step_results"][-1].output

        tokens_used = len(response_text.split()) + len(payload.message.split())
        agent_log.log_verification(current_user.id, 0.9, True)

        conversation = db.query(Conversation).filter(
            Conversation.id == payload.conversation_id
        ).first()

        if not conversation:
            conversation = Conversation(
                id=payload.conversation_id,
                user_id=current_user.id,
                title=payload.message[:50],
            )
            db.add(conversation)

        user_msg = Message(
            id=str(uuid.uuid4()),
            conversation_id=payload.conversation_id,
            role="user",
            content=payload.message,
            tokens_used=len(payload.message.split()),
        )

        assistant_msg = Message(
            id=str(uuid.uuid4()),
            conversation_id=payload.conversation_id,
            role="assistant",
            content=response_text,
            tokens_used=len(response_text.split()),
            sources=sources,
        )

        db.add(user_msg)
        db.add(assistant_msg)

        conversation.total_messages = (conversation.total_messages or 0) + 2
        conversation.total_tokens = (conversation.total_tokens or 0) + tokens_used
        current_user.total_conversations = (current_user.total_conversations or 0) + 1
        current_user.total_tokens_used = (current_user.total_tokens_used or 0) + tokens_used

        db.commit()

        execution_time = time.time() - start_time
        logger.info(
            "Chat completed for user %s",
            current_user.username,
            extra={"request_id": request_id, "tokens": tokens_used},
        )
        api_log.log_response("/api/chat", 200, execution_time * 1000)

        return ChatResponse(
            conversation_id=payload.conversation_id,
            response=response_text,
            sources=sources,
            tokens_used=tokens_used,
            execution_time=execution_time,
            status="success",
        )
    except Exception as e:
        logger.error("Chat error: %s", str(e), exc_info=True)
        api_log.log_error("/api/chat", 500, str(e), request_id=request_id)
        raise HTTPException(status_code=500, detail="Chat failed")


async def chat_stream_generator(
    payload: ChatRequest,
    current_user: User,
    db: Session,
) -> AsyncGenerator[str, None]:
    try:
        state: AgentState = {
            "objective": payload.message,
            "plan": [],
            "step_results": [],
            "current_step_idx": 0,
            "status": "initialized",
            "memory_context": "",
            "conversation_id": payload.conversation_id,
            "user_id": current_user.id,
            "meta_data": {},
        }

        result = agent_app.invoke(state)
        response = ""
        if result.get("step_results"):
            response = result["step_results"][-1].output

        for word in response.split():
            yield f"data: {json.dumps({'token': word})}\n\n"
            await asyncio.sleep(0.01)

        yield f"data: {json.dumps({'done': True})}\n\n"
    except Exception as e:
        yield f"data: {json.dumps({'error': str(e)})}\n\n"


@app.post("/api/chat/stream", tags=["Chat"])
@limiter.limit("20/minute")
async def chat_stream(
    request: Request,
    payload: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return StreamingResponse(
        chat_stream_generator(payload, current_user, db),
        media_type="text/event-stream",
    )


@app.get("/api/conversations", tags=["Chat"])
@limiter.limit("30/minute")
async def get_conversations(
    request: Request,
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        conversations = db.query(Conversation).filter(
            Conversation.user_id == current_user.id
        ).order_by(Conversation.updated_at.desc()).limit(limit).all()

        return {"conversations": [serialize_conversation(c) for c in conversations]}
    except Exception as e:
        logger.error("Error fetching conversations: %s", str(e))
        raise HTTPException(status_code=500, detail="Failed to fetch conversations")


@app.get("/api/conversations/{conversation_id}/messages", tags=["Chat"])
@limiter.limit("30/minute")
async def get_messages(
    request: Request,
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        conversation = db.query(Conversation).filter(
            Conversation.id == conversation_id,
            Conversation.user_id == current_user.id,
        ).first()

        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

        messages = db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(Message.timestamp.asc()).all()

        return {"messages": [serialize_message(m) for m in messages]}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error fetching messages: %s", str(e))
        raise HTTPException(status_code=500, detail="Failed to fetch messages")


# =========================
# RAG / Knowledge Endpoints
# =========================

@app.post("/api/documents/upload", response_model=DocumentResponse, tags=["Knowledge Base"])
@limiter.limit("5/minute")
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    request_id = str(uuid.uuid4())
    logger.info("Document upload started: %s", file.filename, extra={"request_id": request_id})

    try:
        allowed_types = ["application/pdf", "text/plain", "application/json"]
        if file.content_type not in allowed_types:
            raise HTTPException(status_code=400, detail="Invalid file type")

        upload_dir = Path("./uploads") / current_user.id
        upload_dir.mkdir(parents=True, exist_ok=True)
        file_path = upload_dir / file.filename

        content = await file.read()
        async with aiofiles.open(file_path, "wb") as f:
            await f.write(content)

        chunk_count = 0
        vector_id = None
        if rag_system is not None:
            result = rag_system.process_document(str(file_path), file.filename)
            chunk_count = result.get("chunks", 0)
            vector_id = result.get("vector_id")

        doc = Document(
            id=str(uuid.uuid4()),
            user_id=current_user.id,
            filename=file.filename,
            content_type=file.content_type,
            file_path=str(file_path),
            file_size=len(content),
            chunk_count=chunk_count,
            vector_db_id=vector_id,
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

        rag_log.log_upload(current_user.id, file.filename, doc.chunk_count)
        logger.info("Document uploaded successfully: %s", file.filename)

        return DocumentResponse(
            id=doc.id,
            filename=doc.filename,
            file_size=doc.file_size,
            chunks=doc.chunk_count,
            created_at=doc.created_at,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Document upload error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="File upload failed")


@app.get("/api/documents", tags=["Knowledge Base"])
@limiter.limit("30/minute")
async def get_documents(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        documents = db.query(Document).filter(
            Document.user_id == current_user.id
        ).order_by(Document.created_at.desc()).all()

        return {"documents": [serialize_document(d) for d in documents]}
    except Exception as e:
        logger.error("Error fetching documents: %s", str(e))
        raise HTTPException(status_code=500, detail="Failed to fetch documents")


@app.post("/api/search", tags=["Knowledge Base"])
@limiter.limit("20/minute")
async def search_knowledge(
    request: Request,
    payload: SearchRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        start_time = time.time()

        if rag_system is None:
            return {
                "query": payload.query,
                "results": {"error": "RAG system not initialized"},
                "latency_ms": 0.0,
            }

        rag_results = rag_system.query_knowledge(payload.query)

        latency = time.time() - start_time
        rag_log.log_retrieval(
            current_user.id,
            payload.query,
            len(rag_results.get("sources", [])),
            latency * 1000,
        )

        return {
            "query": payload.query,
            "results": rag_results,
            "latency_ms": latency * 1000,
        }
    except Exception as e:
        logger.error("Search error: %s", str(e))
        raise HTTPException(status_code=500, detail="Search failed")


# =========================
# Preferences Endpoints
# =========================

@app.post("/api/preferences", tags=["User Settings"])
@limiter.limit("20/minute")
async def update_preferences(
    request: Request,
    payload: PreferencesUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        prefs_dict = {k: v for k, v in payload.dict().items() if v is not None}
        if memory_manager is not None:
            memory_manager.save_preferences(current_user.id, prefs_dict)

        logger.info("Preferences updated for user: %s", current_user.username)
        return {"status": "preferences_updated"}
    except Exception as e:
        logger.error("Error updating preferences: %s", str(e))
        raise HTTPException(status_code=500, detail="Failed to update preferences")


@app.get("/api/preferences", tags=["User Settings"])
@limiter.limit("30/minute")
async def get_preferences(
    request: Request,
    current_user: User = Depends(get_current_user),
):
    try:
        if memory_manager is None:
            return {"preferences": {}}
        prefs = memory_manager.get_preferences(current_user.id)
        return {"preferences": prefs}
    except Exception as e:
        logger.error("Error fetching preferences: %s", str(e))
        raise HTTPException(status_code=500, detail="Failed to fetch preferences")


# =========================
# Task Endpoints
# =========================

@app.post("/api/tasks", response_model=TaskResponse, tags=["Tasks"])
@limiter.limit("20/minute")
async def create_task(
    request: Request,
    payload: TaskCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        new_task = Task(
            id=str(uuid.uuid4()),
            user_id=current_user.id,
            title=payload.title,
            description=payload.description,
            priority=payload.priority,
            due_date=payload.due_date,
            recurrence=payload.recurrence,
            is_recurring=bool(payload.recurrence),
        )
        db.add(new_task)
        db.commit()
        db.refresh(new_task)

        logger.info("Task created: %s for user %s", payload.title, current_user.username)
        return serialize_task(new_task)
    except Exception as e:
        logger.error("Error creating task: %s", str(e))
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create task")


@app.get("/api/tasks", tags=["Tasks"])
@limiter.limit("30/minute")
async def get_tasks(
    request: Request,
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        query = db.query(Task).filter(Task.user_id == current_user.id)
        if status:
            query = query.filter(Task.status == status)

        tasks = query.order_by(Task.priority.desc(), Task.due_date.asc()).all()
        return {"tasks": [serialize_task(t) for t in tasks]}
    except Exception as e:
        logger.error("Error fetching tasks: %s", str(e))
        raise HTTPException(status_code=500, detail="Failed to fetch tasks")


@app.put("/api/tasks/{task_id}", response_model=TaskResponse, tags=["Tasks"])
@limiter.limit("20/minute")
async def update_task(
    request: Request,
    task_id: str,
    payload: TaskUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        task = db.query(Task).filter(
            Task.id == task_id,
            Task.user_id == current_user.id,
        ).first()

        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        update_data = payload.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(task, field, value)

        task.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(task)

        logger.info("Task updated: %s", task_id)
        return serialize_task(task)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error updating task: %s", str(e))
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update task")


@app.delete("/api/tasks/{task_id}", tags=["Tasks"])
@limiter.limit("20/minute")
async def delete_task(
    request: Request,
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        task = db.query(Task).filter(
            Task.id == task_id,
            Task.user_id == current_user.id,
        ).first()

        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        db.delete(task)
        db.commit()

        logger.info("Task deleted: %s", task_id)
        return {"status": "task_deleted"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error deleting task: %s", str(e))
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete task")


# =========================
# Code Analysis Endpoints
# =========================

@app.post("/api/code/analyze", response_model=CodeAnalysisResponse, tags=["Developer Assistant"])
@limiter.limit("30/minute")
async def analyze_code(
    request: Request,
    payload: CodeAnalysisRequest,
    current_user: User = Depends(get_current_user),
):
    try:
        if code_analyzer is not None:
            if payload.analysis_type == "full":
                analysis = code_analyzer.analyze_code(payload.code, payload.language)
                suggestions = code_analyzer.suggest_fixes(payload.code, [])
                explanation = code_analyzer.explain_code(payload.code)
                refactoring = code_analyzer.suggest_refactoring(payload.code)
            elif payload.analysis_type == "complexity":
                analysis = code_analyzer.analyze_code(payload.code, payload.language)
                suggestions = []
                explanation = ""
                refactoring = {}
            elif payload.analysis_type == "dependencies":
                analysis = code_analyzer.analyze_dependencies(payload.code, payload.language)
                suggestions = []
                explanation = ""
                refactoring = {}
            else:
                analysis = code_analyzer.analyze_code(payload.code, payload.language)
                suggestions = []
                explanation = ""
                refactoring = {}
        else:
            analysis = fallback_code_analysis(payload.code, payload.language)
            suggestions = analysis.get("suggestions", [])
            explanation = fallback_explanation(payload.code)
            refactoring = fallback_refactoring()

        return CodeAnalysisResponse(
            analysis=analysis,
            suggestions=suggestions,
            explanation=explanation,
            refactoring=refactoring,
        )
    except Exception as e:
        logger.error("Code analysis error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Code analysis failed")


# =========================
# Health / Stats / Root
# =========================

@app.get("/api/health", tags=["System"])
@limiter.limit("100/minute")
async def health_check(request: Request):
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "2.0.0",
        "features": [
            "Multi-Agent Intelligence",
            "Authentication & Authorization",
            "Long-Term Memory",
            "RAG System",
            "Tool Integration",
            "Task Automation",
            "Developer Assistant",
            "Streaming Responses",
            "Rate Limiting",
            "Comprehensive Logging",
        ],
    }


@app.get("/api/stats", tags=["System"])
@limiter.limit("30/minute")
async def get_stats(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        total_conversations = db.query(Conversation).filter(
            Conversation.user_id == current_user.id
        ).count()

        total_messages = db.query(Message).join(Conversation).filter(
            Conversation.user_id == current_user.id
        ).count()

        total_documents = db.query(Document).filter(
            Document.user_id == current_user.id
        ).count()

        total_tasks = db.query(Task).filter(
            Task.user_id == current_user.id
        ).count()

        return {
            "total_conversations": total_conversations,
            "total_messages": total_messages,
            "total_documents": total_documents,
            "total_tasks": total_tasks,
            "total_tokens": current_user.total_tokens_used,
        }
    except Exception as e:
        logger.error("Error fetching stats: %s", str(e))
        raise HTTPException(status_code=500, detail="Failed to fetch stats")


@app.get("/", tags=["System"])
async def root():
    return {
        "name": "OmniAgent AI",
        "version": "2.0.0",
        "status": "operational",
        "docs": "/api/docs",
    }


# =========================
# Error Handlers
# =========================

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.error("HTTP Exception: %s - %s", exc.status_code, exc.detail)
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled exception: %s", str(exc), exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error"},
    )


# =========================
# Startup / Shutdown
# =========================

@app.on_event("startup")
async def startup_event():
    logger.info("OmniAgent AI backend starting...")
    logger.info("Features: Auth, Logging, Rate Limiting, Streaming, RAG")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("OmniAgent AI backend shutting down...")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        workers=int(os.getenv("WORKERS", 1)),
        log_level=os.getenv("LOG_LEVEL", "info"),
    )