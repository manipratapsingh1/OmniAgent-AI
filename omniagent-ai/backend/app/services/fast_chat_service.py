"""
Fast Chat Service - Simple RAG-enabled chat without complex agent pipeline
Designed for quick responses with document context
"""

import time
import json
import structlog
import asyncio
from typing import Optional, AsyncIterator
from sqlmodel import Session
from datetime import datetime, timezone

from app.models.conversation import Conversation
from app.models.message import Message
from app.repositories.conversation_repo import ConversationRepo
from app.schemas.chat import ChatRequest, ChatResponse, Citation
from app.rag.retriever import retrieve
from app.llm.ollama_client import ollama
from app.llm.prompts import CHAT_SYSTEM
from app.utils.citations import get_citations_with_fallback, validate_citation_accuracy
from app.memory.short_term import append as mem_append
from app.services.memory_service import MemoryService
from app.config import get_settings
from app import metrics as app_metrics

log = structlog.get_logger("chat_fast")
settings = get_settings()


class FastChatService:
    """Simplified chat service for fast responses with RAG support"""
    
    def __init__(self, db: Session):
        self.db = db
        self.repo = ConversationRepo(db)
        self.memory = MemoryService(db)

    def _ensure_conversation(self, user_id: int, conv_id: Optional[int], model: Optional[str]) -> Conversation:
        """Get or create conversation"""
        if conv_id and conv_id > 0:
            conv = self.repo.get(conv_id)
            if not conv or conv.user_id != user_id:
                log.warning("chat.conversation_access_denied", user_id=user_id, conv_id=conv_id)
                raise ValueError("Conversation not found")
            return conv
        conv = Conversation(user_id=user_id, model=model or settings.OLLAMA_FAST_MODEL)
        saved_conv = self.repo.add(conv)
        log.info("chat.conversation_created", user_id=user_id, conv_id=saved_conv.id)
        return saved_conv

    async def chat(self, user_id: int, req: ChatRequest) -> ChatResponse:
        """
        Fast chat with optional RAG support.
        Skips complex agent pipeline for speed.
        """
        conv = self._ensure_conversation(user_id, req.conversation_id, req.model or "phi3:mini")
        log.info(
            "chat_fast.start",
            user_id=user_id,
            conv_id=conv.id,
            message_len=len(req.message),
            use_rag=req.use_rag,
        )

        # Save user message
        user_msg = Message(conversation_id=conv.id, role="user", content=req.message)
        self.db.add(user_msg)
        self.db.commit()
        self.db.refresh(user_msg)
        await mem_append(conv.id, "user", req.message)

        # Retrieve context if RAG enabled
        context_text = ""
        all_retrieved_sources = []
        
        if req.use_rag:
            t0 = time.perf_counter()
            try:
                all_retrieved_sources = await retrieve(
                    user_id=user_id,
                    query=req.message,
                    k=4,
                    db=self.db,
                )

                if all_retrieved_sources:
                    context_text = "\n\n".join(
                        [f"[doc:{c['document_id']}#{c['chunk_index']}] {c['text']}" for c in all_retrieved_sources]
                    )
                    log.info(
                        "chat_fast.rag_retrieved",
                        duration_ms=int((time.perf_counter() - t0) * 1000),
                        chunks=len(all_retrieved_sources),
                    )
                else:
                    log.info("chat_fast.rag_no_results", user_id=user_id)
            except Exception as e:
                log.warning("chat_fast.rag_retrieval_failed", error=str(e))
                context_text = ""
                all_retrieved_sources = []
        
        # Get learned facts about the user
        facts = self.memory.get_learned_facts(user_id)

        system_prompt = req.system_prompt or CHAT_SYSTEM
        if facts:
            fact_str = "\n".join([f"- {f.fact}" for f in facts])
            system_prompt += f"\n\nKnown facts about the user:\n{fact_str}"

        # Generate response using improved prompt
        try:
            if context_text:
                prompt = f"""User Question: {req.message}

Document Context:
{context_text}

Instructions: Answer using the provided documents. Always cite sources as [doc:id#chunk]. If information is not in documents, say so clearly."""
            else:
                prompt = f"User Question: {req.message}\n\nPlease answer this question concisely."
            
            prompt_tokens = max(1, len(prompt) // 4)
            app_metrics.CHAT_PROMPT_TOKENS.labels(endpoint="chat").observe(prompt_tokens)
            t0 = time.perf_counter()
            answer = await ollama.generate(
                    prompt=prompt,
                    model=req.model or settings.OLLAMA_FAST_MODEL,
                    system=system_prompt,
                    images=req.images,
                )
            response_tokens = max(1, len(answer) // 4)
            app_metrics.CHAT_RESPONSE_TOKENS.labels(endpoint="chat").observe(response_tokens)
            
            duration_ms = int((time.perf_counter() - t0) * 1000)
            log.info(
                "chat_fast.response_generated",
                duration_ms=duration_ms,
                answer_len=len(answer),
            )
            
            if not answer:
                answer = "I couldn't generate a response. Please try again."
                
        except Exception as e:
            log.exception("chat_fast.generation_failed", error=str(e))
            answer = f"Error generating response: {str(e)[:100]}"

        # Extract actual citations from response instead of using all retrieved sources
        cited_sources, was_cited = get_citations_with_fallback(answer, all_retrieved_sources)
        
        # Convert to Citation objects
        sources = [
            Citation(
                document_id=c["document_id"],
                chunk_index=c["chunk_index"],
                snippet=c["text"][:240]
            )
            for c in cited_sources
        ]
        
        # Log citation accuracy
        citation_accuracy = validate_citation_accuracy(answer, cited_sources)
        log.info(
            "chat_fast.citations_extracted",
            citations_in_text=citation_accuracy["citations_in_text"],
            verified_sources=citation_accuracy["verified_sources"],
            accuracy_score=citation_accuracy["accuracy_score"],
        )

        # Save assistant message
        assistant_msg = Message(
            conversation_id=conv.id,
            role="assistant",
            content=answer,
            agent="fast_chat",
            sources=json.dumps([s.model_dump() for s in sources]),
        )
        self.db.add(assistant_msg)

        # Update conversation
        conv.updated_at = datetime.now(timezone.utc)
        if conv.title == "New Conversation":
            conv.title = (req.message[:48] + ("…" if len(req.message) > 48 else ""))
        self.db.add(conv)
        self.db.commit()
        self.db.refresh(assistant_msg)

        await mem_append(conv.id, "assistant", answer)

        # Extract facts in background (async)
        asyncio.create_task(self._extract_facts(user_id, req.message))

        log.info(
            "chat_fast.complete",
            user_id=user_id,
            conv_id=conv.id,
            sources_count=len(sources),
            was_cited=was_cited,
        )

        return ChatResponse(
            conversation_id=conv.id,
            message_id=assistant_msg.id,
            content=answer,
            sources=sources,
            trace=[],  # No trace for fast chat
        )

    async def _extract_facts(self, user_id: int, message: str):
        """Extract facts about the user from their message using LLM."""
        try:
            # Simple extraction prompt
            extraction_prompt = f"""Extract 1-3 simple facts about the user from this message if they are sharing preferences, bio info, or interests. 
If no new facts are found, return 'NONE'.
Format: Just the facts, one per line.
User Message: {message}"""
            
            resp = await ollama.generate(
                prompt=extraction_prompt,
                model=settings.OLLAMA_FAST_MODEL,
                system="You are a data extraction assistant. Be concise."
            )
            
            if "NONE" in resp.upper():
                return
            
            facts = [f.strip("- ").strip() for f in resp.split("\n") if f.strip() and "NONE" not in f.upper()]
            for fact in facts:
                if len(fact) > 5: # Avoid noise
                    self.memory.store_learned_fact(user_id, fact)
                    
        except Exception as e:
            log.warning("memory.extraction_failed", error=str(e))

    async def stream(self, user_id: int, req: ChatRequest) -> AsyncIterator[dict]:
        """Stream a fast chat response while saving the conversation and final message."""
        conv = self._ensure_conversation(user_id, req.conversation_id, req.model or "phi3:mini")
        log.info(
            "chat_fast.stream.start",
            user_id=user_id,
            conv_id=conv.id,
            message_len=len(req.message),
            use_rag=req.use_rag,
        )

        user_msg = Message(conversation_id=conv.id, role="user", content=req.message)
        self.db.add(user_msg)
        self.db.commit()
        self.db.refresh(user_msg)
        await mem_append(conv.id, "user", req.message)

        context_text = ""
        all_retrieved_sources = []
        if req.use_rag:
            try:
                all_retrieved_sources = await retrieve(
                    user_id=user_id,
                    query=req.message,
                    k=4,
                    db=self.db,
                )
                if all_retrieved_sources:
                    context_text = "\n\n".join(
                        [f"[doc:{c['document_id']}#{c['chunk_index']}] {c['text']}" for c in all_retrieved_sources]
                    )
                log.info("chat_fast.stream.rag_retrieved", chunks=len(all_retrieved_sources))
            except Exception as e:
                log.warning("chat_fast.stream.rag_failed", error=str(e))
                context_text = ""
                all_retrieved_sources = []

        system_prompt = req.system_prompt or CHAT_SYSTEM

        if context_text:
            prompt = f"""User Question: {req.message}

Document Context:
{context_text}

Instructions: Answer using the provided documents. Always cite sources as [doc:id#chunk]. If information is not in documents, say so clearly and cite only the sources you used."""
        else:
            prompt = f"User Question: {req.message}\n\nPlease answer this question concisely. If you cannot answer confidently, say you don't know."

        prompt_tokens = max(1, len(prompt) // 4)
        app_metrics.CHAT_PROMPT_TOKENS.labels(endpoint="chat_stream").observe(prompt_tokens)
        t0 = time.perf_counter()
        first_token_recorded = False

        yield {
            "type": "metadata",
            "data": {
                "conversation_id": conv.id,
                "sources": [
                    {
                        "document_id": c["document_id"],
                        "chunk_index": c["chunk_index"],
                        "snippet": c["text"][:240],
                    }
                    for c in all_retrieved_sources
                ],
            },
        }

        answer = ""
        try:
            async for token in ollama.stream(
                prompt=prompt,
                model=req.model or settings.OLLAMA_FAST_MODEL,
                system=system_prompt,
                images=req.images,
            ):
                normalized = str(token or "")
                if normalized:
                    if not first_token_recorded:
                        first_token_recorded = True
                        app_metrics.CHAT_FIRST_TOKEN_LATENCY.labels(endpoint="chat_stream").observe(
                            time.perf_counter() - t0
                        )
                    answer += normalized
                    yield {"type": "token", "content": normalized}

            if not answer.strip():
                answer = "I couldn't generate a response. Please try again."
                yield {"type": "token", "content": answer}

        except Exception as e:
            error_text = f"Error generating response: {str(e)[:100]}"
            yield {"type": "token", "content": error_text}
            answer = error_text

        # Extract actual citations from response
        cited_sources, was_cited = get_citations_with_fallback(answer, all_retrieved_sources)
        
        # Convert to Citation objects
        sources = [
            Citation(
                document_id=c["document_id"],
                chunk_index=c["chunk_index"],
                snippet=c["text"][:240],
            )
            for c in cited_sources
        ]

        response_tokens = max(1, len(answer) // 4)
        app_metrics.CHAT_RESPONSE_TOKENS.labels(endpoint="chat_stream").observe(response_tokens)

        assistant_msg = Message(
            conversation_id=conv.id,
            role="assistant",
            content=answer,
            agent="fast_chat",
            sources=json.dumps([s.model_dump() for s in sources]),
        )
        self.db.add(assistant_msg)

        conv.updated_at = datetime.now(timezone.utc)
        if conv.title == "New Conversation":
            conv.title = (req.message[:48] + ("…" if len(req.message) > 48 else ""))
        self.db.add(conv)
        self.db.commit()
        self.db.refresh(assistant_msg)
        await mem_append(conv.id, "assistant", answer)

        # Extract facts in background (async)
        asyncio.create_task(self._extract_facts(user_id, req.message))

        log.info(
            "chat_fast.stream.complete",
            user_id=user_id,
            sources_count=len(sources),
            was_cited=was_cited,
        )

        yield {
            "type": "done",
            "conversation_id": conv.id,
            "message_id": assistant_msg.id,
            "sources": [s.model_dump() for s in sources],
        }
