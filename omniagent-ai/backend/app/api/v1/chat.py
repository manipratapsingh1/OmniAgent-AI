from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlmodel import Session
import hashlib
import structlog
import time
import json

from app.deps import db_session, current_user
from app.models.user import User
from app.schemas.chat import ChatRequest, ChatResponse, Citation
from app.services.chat_service import ChatService
from app.services.fast_chat_service import FastChatService
from app.llm.ollama_client import ollama
from app.rag.retriever import retrieve
from app.llm.prompts import RESEARCH_SYSTEM
from app.utils.performance import get_response_cache, measure_time
from app.config import get_settings
from app import metrics as app_metrics

router = APIRouter()

DEFAULT_FAST_MODEL = "phi3:mini"

# Global response cache
_cache = get_response_cache()


def _normalize_token(token) -> str:
    """
    Normalize different token shapes returned by Ollama streaming.
    Supports plain strings and dict-style chunks.
    """
    if token is None:
        return ""

    if isinstance(token, str):
        return token

    if isinstance(token, dict):
        # Check nested message structure first
        message = token.get("message")
        if isinstance(message, dict):
            for key in ("content", "text", "response"):
                value = message.get(key)
                if value is not None:
                    return str(value)

        for key in ("response", "message", "token", "text", "content"):
            value = token.get(key)
            if value is not None:
                if isinstance(value, dict):
                    continue
                return str(value)

    return str(token)


def _generate_cache_key(user_id: int, message: str, model: str) -> str:
    """Generate cache key for chat responses"""
    key_input = f"{user_id}:{message}:{model}"
    return hashlib.md5(key_input.encode()).hexdigest()


@router.post("/", response_model=ChatResponse)
@measure_time("chat.endpoint")
async def chat(
    req: ChatRequest,
    db: Session = Depends(db_session),
    user: User = Depends(current_user),
):
    """
    Fast chat endpoint with optional RAG support.
    Uses simplified pipeline for quick responses (3-10 seconds).
    Set force_fresh=true to bypass caching.
    """
    # Try to get cached response for identical queries
    cache_key = _generate_cache_key(user.id, req.message, req.model or "default")
    cached_response = _cache.get(cache_key)
    
    if cached_response and not req.force_fresh:
        return cached_response

    # Try semantic cache
    if not req.force_fresh:
        from app.utils.semantic_cache import semantic_cache
        try:
            cached_answer = await semantic_cache.get(req.message)
            if cached_answer:
                response = ChatResponse(
                    conversation_id=req.conversation_id or 0,
                    message_id=0,
                    content=cached_answer,
                    sources=[],
                    trace=[]
                )
                _cache.set(cache_key, response, ttl=300)
                return response
        except Exception:
            pass

    # instrument chat endpoint
    try:
        app_metrics.CHAT_REQUESTS.labels(endpoint="chat").inc()
        t0 = time.time()
    except Exception:
        t0 = None
    
    # Use fast chat service for improved performance
    # The FastChatService skips complex agent pipeline and returns results in 3-10 seconds
    service = FastChatService(db)
    response = await service.chat(user.id, req)
    
    # Cache the response (5-minute TTL for identical queries)
    _cache.set(cache_key, response, ttl=300)

    # Store in semantic cache
    if response and response.content:
        from app.utils.semantic_cache import semantic_cache
        try:
            await semantic_cache.set(req.message, response.content)
        except Exception:
            pass

    try:
        if t0 is not None:
            app_metrics.CHAT_LATENCY.labels(endpoint="chat").observe(time.time() - t0)
    except Exception:
        pass
    
    return response


@router.post("/stream")
@measure_time("chat.stream")
async def chat_stream(
    req: ChatRequest,
    db: Session = Depends(db_session),
    user: User = Depends(current_user),
):
    """
    Fast streaming endpoint for live responses using optimized model.
    Returns token events as newline-delimited JSON.
    """
    service = FastChatService(db)

    async def gen():
        try:
            async for event in service.stream(user.id, req):
                yield json.dumps(event) + "\n"
        except Exception as e:
            import structlog
            log = structlog.get_logger("chat_stream")
            log.error("chat_stream.failed", error=str(e))
            yield json.dumps({
                "type": "error",
                "data": {"message": f"Error: {str(e)[:100]}"}
            }) + "\n"

    return StreamingResponse(gen(), media_type="application/x-ndjson")


@router.post("/fast-rag")
@measure_time("chat.fast_rag")
async def fast_rag(
    req: ChatRequest,
    db: Session = Depends(db_session),
    user: User = Depends(current_user),
):
    """
    Fast document Q&A endpoint that bypasses the full agent pipeline.
    Uses RAG + fast model for quick responses to document questions.
    Returns answer in ~10-20 seconds instead of ~60 seconds.
    
    Ideal for: "What does document X say about Y?"
    """
    from app.utils.citations import get_citations_with_fallback
    
    settings = get_settings()
    log = structlog.get_logger("chat_fast_rag")
    
    try:
        # Try cache first
        cache_key = _generate_cache_key(user.id, req.message, "fast-rag")
        cached = _cache.get(cache_key)
        if cached and not req.force_fresh:
            return cached
        
        log.info("fast_rag.start", user_id=user.id, query_len=len(req.message))
        # instrument fast_rag
        try:
            app_metrics.CHAT_REQUESTS.labels(endpoint="fast_rag").inc()
            rag_t0 = time.time()
        except Exception:
            rag_t0 = None
        
        # Quick document retrieval
        all_ctx = await retrieve(user_id=user.id, query=req.message, k=5)
        
        # Build context
        context_text = ""
        if all_ctx:
            context_text = "\n\n".join(
                [f"[doc:{c['document_id']}#{c['chunk_index']}] {c['text']}" for c in all_ctx]
            )
        else:
            context_text = "(no relevant documents found)"
        
        log.info("fast_rag.retrieved", docs=len(all_ctx), context_len=len(context_text))
        
        # Fast answer generation using lightweight model
        prompt = f"User question: {req.message}\n\nDocument context:\n{context_text}\n\nProvide a concise, direct answer based on the documents above. Cite sources as [doc:id#chunk]."
        
        answer = await ollama.generate(
            prompt=prompt,
            model=settings.FAST_RAG_MODEL,
            system=RESEARCH_SYSTEM,
        )
        
        # Extract only the cited sources, not all retrieved ones
        cited_sources, was_cited = get_citations_with_fallback(answer, all_ctx)
        
        sources = [
            Citation(document_id=c["document_id"], chunk_index=c["chunk_index"], snippet=c["text"][:240])
            for c in cited_sources
        ]
        
        response = ChatResponse(
            conversation_id=0,
            message_id=0,
            content=answer,
            sources=sources,
            trace=[],
        )
        
        # Cache response
        _cache.set(cache_key, response, ttl=300)
        
        log.info(
            "fast_rag.complete",
            all_docs=len(all_ctx),
            cited_sources=len(sources),
            answer_len=len(answer),
            was_cited=was_cited,
        )
        try:
            if rag_t0 is not None:
                app_metrics.CHAT_LATENCY.labels(endpoint="fast_rag").observe(time.time() - rag_t0)
        except Exception:
            pass

        return response
    
    except RuntimeError as e:
        log.error("fast_rag.error", error=str(e))
        return ChatResponse(
            conversation_id=0,
            message_id=0,
            content=f"Error: {str(e)}",
            sources=[],
            trace=[],
        )


@router.get("/models")
async def models(_: User = Depends(current_user)):
    return {"models": await ollama.list_models()}


@router.post("/knowledge-assistant")
@measure_time("chat.knowledge_assistant")
async def knowledge_assistant(
    req: ChatRequest,
    db: Session = Depends(db_session),
    user: User = Depends(current_user),
):
    """
    ChatGPT-like Knowledge Assistant.
    
    Hybrid intelligence combining:
    1. Admin-uploaded knowledge base
    2. General LLM knowledge (fallback)
    
    Response priority:
    - If knowledge base has relevant content, use it
    - If no knowledge base match, use general LLM knowledge
    - AI feels like ChatGPT but with company knowledge
    """
    log = structlog.get_logger("knowledge_assistant")
    settings = get_settings()
    
    try:
        app_metrics.CHAT_REQUESTS.labels(endpoint="knowledge_assistant").inc()
        t0 = time.time()
        
        # Import AI service
        from app.services.ai.service import AIService
        
        # Create AI service with knowledge base
        ai_service = AIService(db=db, provider="ollama")

        # Query with hybrid intelligence
        result = await ai_service.query(
            question=req.message.strip(),
            model=req.model or settings.OLLAMA_DEFAULT_MODEL,
            provider="ollama",
            search_knowledge_base=True,
            k=5,
            system_prompt=req.system_prompt,
        )

        # Convert result to ChatResponse format
        sources = [
            Citation(
                document_id=source.get("document_id"),
                chunk_index=source.get("chunk_index"),
                snippet=source.get("text", "")[:240]
            )
            for source in result.get("sources", [])
        ]
        
        response = ChatResponse(
            conversation_id=req.conversation_id or 0,
            message_id=0,
            content=result["answer"],
            sources=sources,
            trace=[],
        )
        
        log.info(
            "knowledge_assistant.complete",
            used_kb=result.get("used_knowledge_base", False),
            sources=len(sources),
            answer_len=len(result["answer"]),
        )
        
        try:
            if t0 is not None:
                app_metrics.CHAT_LATENCY.labels(endpoint="knowledge_assistant").observe(time.time() - t0)
        except Exception:
            pass
        
        return response
        
    except Exception as e:
        log.error("knowledge_assistant.error", error=str(e), question=req.message)
        return ChatResponse(
            conversation_id=req.conversation_id or 0,
            message_id=0,
            content=f"Error generating response: {str(e)[:100]}",
            sources=[],
            trace=[],
        )


@router.post("/knowledge-assistant/stream")
@measure_time("chat.knowledge_assistant_stream")
async def knowledge_assistant_stream(
    req: ChatRequest,
    db: Session = Depends(db_session),
    user: User = Depends(current_user),
):
    """
    Streaming version of Knowledge Assistant for real-time responses.
    
    Yields:
    1. Metadata with sources (knowledge base matches)
    2. Streamed response chunks
    """
    log = structlog.get_logger("knowledge_assistant_stream")
    settings = get_settings()
    
    async def gen():
        try:
            # Import AI service
            from app.services.ai.service import AIService
            
            # Create AI service
            ai_service = AIService(db=db, provider="ollama")
            
            # Stream with hybrid intelligence
            async for result in ai_service.stream_query(
                question=req.message.strip(),
                model=req.model or settings.OLLAMA_DEFAULT_MODEL,
                provider="ollama",
                search_knowledge_base=True,
                k=5,
                system_prompt=req.system_prompt,
            ):
                # Convert result to JSON and stream
                import orjson
                yield orjson.dumps(result).decode() + "\n"
                
        except Exception as e:
            log.error("knowledge_assistant_stream.error", error=str(e))
            import orjson
            error_result = {
                "type": "error",
                "data": {"message": str(e)}
            }
            yield orjson.dumps(error_result).decode() + "\n"
    
    return StreamingResponse(gen(), media_type="application/x-ndjson")