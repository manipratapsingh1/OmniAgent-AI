"""
Fast Chat Service - Hybrid Knowledge Engine powered chat
Uses intelligent knowledge routing across documents, KB, memory, and AI knowledge.
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
from app.llm.ollama_client import ollama
from app.llm.prompts import CHAT_SYSTEM
from app.utils.citations import get_citations_with_fallback, validate_citation_accuracy
from app.memory.short_term import append as mem_append
from app.services.memory_service import MemoryService
from app.services.ai.hybrid_knowledge_engine import HybridKnowledgeEngine, KnowledgeMode
from app.utils.context_compression import compress_context, deduplicate_chunks
from app.config import get_settings
from app import metrics as app_metrics

log = structlog.get_logger("chat_fast")
settings = get_settings()


class FastChatService:
    """Hybrid knowledge-powered chat service for fast, accurate responses."""

    def __init__(self, db: Session):
        self.db = db
        self.repo = ConversationRepo(db)
        self.memory = MemoryService(db)
        self.knowledge_engine = HybridKnowledgeEngine(db)

    def _ensure_conversation(self, user_id: int, conv_id: Optional[int], model: Optional[str]) -> Conversation:
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

    def _resolve_mode(self, req: ChatRequest) -> KnowledgeMode:
        if not req.use_rag:
            return KnowledgeMode.AI_ONLY
        mode_str = req.knowledge_mode or "auto"
        try:
            return KnowledgeMode(mode_str)
        except ValueError:
            return KnowledgeMode.AUTO

    def _build_citations(
        self,
        answer: str,
        all_sources: list,
    ) -> tuple[list[Citation], bool]:
        cited_sources, was_cited = get_citations_with_fallback(answer, all_sources)
        enriched = self.knowledge_engine.enrich_citations(cited_sources)
        sources = [
            Citation(
                document_id=c["document_id"],
                chunk_index=c["chunk_index"],
                snippet=c.get("snippet", c.get("text", "")[:240]),
                document_name=c.get("document_name"),
                page_number=c.get("page_number"),
                section=c.get("section"),
                confidence_score=c.get("confidence_score"),
            )
            for c in enriched
        ]
        return sources, was_cited

    async def chat(self, user_id: int, req: ChatRequest) -> ChatResponse:
        conv = self._ensure_conversation(user_id, req.conversation_id, req.model or "phi3:mini")
        mode = self._resolve_mode(req)

        log.info(
            "chat_fast.start",
            user_id=user_id,
            conv_id=conv.id,
            message_len=len(req.message),
            use_rag=req.use_rag,
            knowledge_mode=mode.value,
        )

        # Security: validate and sanitize user input
        sanitized_message = req.message
        try:
            from app.services.ai.safety_guard import get_safety_guard
            safety = get_safety_guard()
            validation = safety.validate_chat_input(req.message)
            if not validation["ok"]:
                raise ValueError(validation.get("error", "Invalid message"))
            sanitized_message = validation["message"]
            if validation.get("injection_detected"):
                log.warning("chat_fast.injection_flagged", user_id=user_id)
        except ValueError:
            raise  # Re-raise validation errors
        except Exception as e:
            # Safety guard failure should not block chat
            log.warning("chat_fast.safety_guard_failed", error=str(e))
            sanitized_message = req.message

        user_msg = Message(conversation_id=conv.id, role="user", content=sanitized_message)
        self.db.add(user_msg)
        self.db.commit()
        self.db.refresh(user_msg)
        await mem_append(conv.id, "user", sanitized_message)

        all_retrieved_sources = []
        knowledge_result = None

        if req.use_rag:
            t0 = time.perf_counter()
            try:
                # Cap retrieval at 10 seconds to prevent blocking
                knowledge_result = await asyncio.wait_for(
                    self.knowledge_engine.retrieve_and_decide(
                        user_id=user_id,
                        query=sanitized_message,
                        k=6,
                        mode=mode,
                        conversation_id=conv.id,
                    ),
                    timeout=10.0,
                )
                all_retrieved_sources = deduplicate_chunks(
                    compress_context(knowledge_result["chunks"])
                )
                log.info(
                    "chat_fast.hybrid_retrieved",
                    duration_ms=int((time.perf_counter() - t0) * 1000),
                    case=knowledge_result["case"].value,
                    confidence=knowledge_result["confidence"],
                    chunks=len(all_retrieved_sources),
                )
            except asyncio.TimeoutError:
                log.warning("chat_fast.hybrid_retrieval_timeout", user_id=user_id)
                all_retrieved_sources = []
                knowledge_result = None
            except Exception as e:
                log.warning("chat_fast.hybrid_retrieval_failed", error=str(e))
                all_retrieved_sources = []
                knowledge_result = None

        facts = self.memory.get_learned_facts(user_id)
        base_system = req.system_prompt or CHAT_SYSTEM
        if facts:
            fact_str = "\n".join([f"- {f.fact}" for f in facts])
            base_system += f"\n\nKnown facts about the user:\n{fact_str}"

        try:
            safety_hardening = ""
            try:
                from app.services.ai.safety_guard import get_safety_guard
                safety = get_safety_guard()
                safety_hardening = safety.build_system_hardening()
            except Exception:
                pass  # Safety hardening is optional

            if knowledge_result and req.use_rag:
                user_prompt, system_instructions = self.knowledge_engine.build_prompt(
                    sanitized_message, knowledge_result
                )
                system_prompt = base_system + "\n" + system_instructions + safety_hardening
            elif all_retrieved_sources:
                context_text = "\n\n".join(
                    [f"[doc:{c['document_id']}#{c['chunk_index']}] {c['text']}" for c in all_retrieved_sources]
                )
                user_prompt = f"User Question: {sanitized_message}\n\nDocument Context:\n{context_text}"
                system_prompt = base_system + safety_hardening
            else:
                user_prompt = f"User Question: {sanitized_message}\n\nPlease answer this question concisely."
                system_prompt = base_system + safety_hardening

            prompt_tokens = max(1, len(user_prompt) // 4)
            app_metrics.CHAT_PROMPT_TOKENS.labels(endpoint="chat").observe(prompt_tokens)
            t0 = time.perf_counter()
            model_name = req.model or settings.OLLAMA_FAST_MODEL
            provider_name = None
            if model_name:
                model_lower = model_name.lower()
                if any(x in model_lower for x in ["gpt", "openai"]):
                    provider_name = "openai"
                elif any(x in model_lower for x in ["claude", "anthropic"]):
                    provider_name = "anthropic"
                elif any(x in model_lower for x in ["gemini"]):
                    provider_name = "gemini"
                elif any(x in model_lower for x in ["groq", "mixtral"]):
                    provider_name = "groq"

            if provider_name:
                from app.services.ai.service import AIService
                ai_service = AIService(db=self.db)
                answer = await ai_service.generate(
                    prompt=user_prompt,
                    provider=provider_name,
                    model=model_name,
                    system=system_prompt,
                    images=req.images,
                )
            else:
                answer = await ollama.generate(
                    prompt=user_prompt,
                    model=model_name,
                    system=system_prompt,
                    images=req.images,
                )
            response_tokens = max(1, len(answer) // 4)
            app_metrics.CHAT_RESPONSE_TOKENS.labels(endpoint="chat").observe(response_tokens)

            duration_ms = int((time.perf_counter() - t0) * 1000)
            log.info("chat_fast.response_generated", duration_ms=duration_ms, answer_len=len(answer))

            if not answer:
                answer = "I couldn't generate a response. Please try again."

        except Exception as e:
            log.exception("chat_fast.generation_failed", error=str(e))
            # Never show raw error to user — provide a helpful fallback
            answer = "Error generating response. Please try again in a moment."

        sources, was_cited = self._build_citations(answer, all_retrieved_sources)

        citation_accuracy = validate_citation_accuracy(answer, [s.model_dump() for s in sources])
        log.info(
            "chat_fast.citations_extracted",
            citations_in_text=citation_accuracy["citations_in_text"],
            verified_sources=citation_accuracy["verified_sources"],
            accuracy_score=citation_accuracy["accuracy_score"],
        )

        assistant_msg = Message(
            conversation_id=conv.id,
            role="assistant",
            content=answer,
            agent="hybrid_chat",
            sources=json.dumps([s.model_dump() for s in sources]),
        )
        self.db.add(assistant_msg)

        conv.updated_at = datetime.now(timezone.utc)
        if conv.title == "New Conversation":
            conv.title = (sanitized_message[:48] + ("…" if len(sanitized_message) > 48 else ""))
        self.db.add(conv)
        self.db.commit()
        self.db.refresh(assistant_msg)

        await mem_append(conv.id, "assistant", answer)
        asyncio.create_task(self._extract_facts(user_id, sanitized_message))

        log.info(
            "chat_fast.complete",
            user_id=user_id,
            conv_id=conv.id,
            sources_count=len(sources),
            was_cited=was_cited,
            case=knowledge_result["case"].value if knowledge_result else "none",
        )

        return ChatResponse(
            conversation_id=conv.id,
            message_id=assistant_msg.id,
            content=answer,
            sources=sources,
            trace=[],
        )

    async def _extract_facts(self, user_id: int, message: str):
        try:
            extraction_prompt = f"""Extract 1-3 simple facts about the user from this message if they are sharing preferences, bio info, or interests. 
If no new facts are found, return 'NONE'.
Format: Just the facts, one per line.
User Message: {message}"""

            resp = await ollama.generate(
                prompt=extraction_prompt,
                model=settings.OLLAMA_FAST_MODEL,
                system="You are a data extraction assistant. Be concise.",
            )

            if "NONE" in resp.upper():
                return

            facts = [f.strip("- ").strip() for f in resp.split("\n") if f.strip() and "NONE" not in f.upper()]
            for fact in facts:
                if len(fact) > 5:
                    self.memory.store_learned_fact(user_id, fact)

        except Exception as e:
            log.warning("memory.extraction_failed", error=str(e))

    async def stream(self, user_id: int, req: ChatRequest) -> AsyncIterator[dict]:
        conv = self._ensure_conversation(user_id, req.conversation_id, req.model or "phi3:mini")
        mode = self._resolve_mode(req)

        log.info(
            "chat_fast.stream.start",
            user_id=user_id,
            conv_id=conv.id,
            knowledge_mode=mode.value,
        )

        sanitized_message = req.message
        try:
            from app.services.ai.safety_guard import get_safety_guard
            safety = get_safety_guard()
            validation = safety.validate_chat_input(req.message)
            if not validation["ok"]:
                raise ValueError(validation.get("error", "Invalid message"))
            sanitized_message = validation["message"]
        except ValueError:
            raise
        except Exception as e:
            log.warning("chat_fast.stream.safety_guard_failed", error=str(e))
            sanitized_message = req.message

        user_msg = Message(conversation_id=conv.id, role="user", content=sanitized_message)
        self.db.add(user_msg)
        self.db.commit()
        self.db.refresh(user_msg)
        await mem_append(conv.id, "user", sanitized_message)

        all_retrieved_sources = []
        knowledge_result = None

        if req.use_rag:
            try:
                knowledge_result = await asyncio.wait_for(
                    self.knowledge_engine.retrieve_and_decide(
                        user_id=user_id,
                        query=sanitized_message,
                        k=6,
                        mode=mode,
                        conversation_id=conv.id,
                    ),
                    timeout=10.0,
                )
                all_retrieved_sources = deduplicate_chunks(
                    compress_context(knowledge_result["chunks"])
                )
            except asyncio.TimeoutError:
                log.warning("chat_fast.stream.hybrid_timeout", user_id=user_id)
            except Exception as e:
                log.warning("chat_fast.stream.hybrid_failed", error=str(e))

        base_system = req.system_prompt or CHAT_SYSTEM

        safety_hardening = ""
        try:
            from app.services.ai.safety_guard import get_safety_guard
            safety = get_safety_guard()
            safety_hardening = safety.build_system_hardening()
        except Exception:
            pass

        if knowledge_result and req.use_rag:
            user_prompt, system_instructions = self.knowledge_engine.build_prompt(
                sanitized_message, knowledge_result
            )
            system_prompt = base_system + "\n" + system_instructions + safety_hardening
        elif all_retrieved_sources:
            context_text = "\n\n".join(
                [f"[doc:{c['document_id']}#{c['chunk_index']}] {c['text']}" for c in all_retrieved_sources]
            )
            user_prompt = f"User Question: {sanitized_message}\n\nDocument Context:\n{context_text}"
            system_prompt = base_system + safety_hardening
        else:
            user_prompt = f"User Question: {sanitized_message}\n\nPlease answer this question concisely."
            system_prompt = base_system + safety_hardening

        prompt_tokens = max(1, len(user_prompt) // 4)
        app_metrics.CHAT_PROMPT_TOKENS.labels(endpoint="chat_stream").observe(prompt_tokens)
        t0 = time.perf_counter()
        first_token_recorded = False

        enriched_preview = self.knowledge_engine.enrich_citations(all_retrieved_sources)
        yield {
            "type": "metadata",
            "data": {
                "conversation_id": conv.id,
                "knowledge_case": knowledge_result["case"].value if knowledge_result else None,
                "confidence": knowledge_result["confidence"] if knowledge_result else "none",
                "sources": [
                    {
                        "document_id": c["document_id"],
                        "chunk_index": c["chunk_index"],
                        "snippet": c.get("snippet", c.get("text", "")[:240]),
                        "document_name": c.get("document_name"),
                        "page_number": c.get("page_number"),
                        "section": c.get("section"),
                        "confidence_score": c.get("confidence_score"),
                    }
                    for c in enriched_preview
                ],
            },
        }

        answer = ""
        try:
            model_name = req.model or settings.OLLAMA_FAST_MODEL
            provider_name = None
            if model_name:
                model_lower = model_name.lower()
                if any(x in model_lower for x in ["gpt", "openai"]):
                    provider_name = "openai"
                elif any(x in model_lower for x in ["claude", "anthropic"]):
                    provider_name = "anthropic"
                elif any(x in model_lower for x in ["gemini"]):
                    provider_name = "gemini"
                elif any(x in model_lower for x in ["groq", "mixtral"]):
                    provider_name = "groq"

            if provider_name:
                from app.services.ai.service import AIService
                ai_service = AIService(db=self.db)
                token_stream = ai_service.stream(
                    prompt=user_prompt,
                    provider=provider_name,
                    model=model_name,
                    system=system_prompt,
                    images=req.images,
                )
            else:
                token_stream = ollama.stream(
                    prompt=user_prompt,
                    model=model_name,
                    system=system_prompt,
                    images=req.images,
                )

            async for token in token_stream:
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

        sources, was_cited = self._build_citations(answer, all_retrieved_sources)

        response_tokens = max(1, len(answer) // 4)
        app_metrics.CHAT_RESPONSE_TOKENS.labels(endpoint="chat_stream").observe(response_tokens)

        assistant_msg = Message(
            conversation_id=conv.id,
            role="assistant",
            content=answer,
            agent="hybrid_chat",
            sources=json.dumps([s.model_dump() for s in sources]),
        )
        self.db.add(assistant_msg)

        conv.updated_at = datetime.now(timezone.utc)
        if conv.title == "New Conversation":
            conv.title = (sanitized_message[:48] + ("…" if len(sanitized_message) > 48 else ""))
        self.db.add(conv)
        self.db.commit()
        self.db.refresh(assistant_msg)
        await mem_append(conv.id, "assistant", answer)
        asyncio.create_task(self._extract_facts(user_id, sanitized_message))

        log.info("chat_fast.stream.complete", sources_count=len(sources), was_cited=was_cited)

        yield {
            "type": "done",
            "conversation_id": conv.id,
            "message_id": assistant_msg.id,
            "sources": [s.model_dump() for s in sources],
        }
