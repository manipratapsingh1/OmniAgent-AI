"""
Hybrid Knowledge Engine — intelligently routes queries across knowledge sources.

Priority order:
1. Uploaded Documents
2. Internal Knowledge Base
3. Conversation Memory
4. Web Search (if enabled)
5. Foundation Model Knowledge
"""
from __future__ import annotations

import re
import time
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import structlog
from sqlmodel import Session, select

from app.config import get_settings
from app.models.document import Document
from app.rag.hybrid_search import (
    assess_retrieval_confidence,
    filter_irrelevant_chunks,
    hybrid_merge,
)
from app.rag.retriever import retrieve, _keyword_search_fallback

log = structlog.get_logger("hybrid_knowledge_engine")
settings = get_settings()


class KnowledgeMode(str, Enum):
    AUTO = "auto"
    DOCUMENTS_ONLY = "documents_only"
    AI_ONLY = "ai_only"


class KnowledgeCase(str, Enum):
    FULL_DOCUMENT = "case_1_full_document"
    PARTIAL_DOCUMENT = "case_2_partial_document"
    NO_DOCUMENT = "case_3_no_document"
    MULTI_DOCUMENT = "case_4_multi_document"
    DOCUMENTS_ONLY = "case_5_documents_only"
    AI_ONLY = "case_6_ai_only"


# Phrases that trigger mode overrides
_DOCUMENTS_ONLY_PATTERNS = [
    r"answer\s+only\s+from\s+(my\s+)?documents?",
    r"use\s+only\s+(my\s+)?documents?",
    r"from\s+(my\s+)?uploaded\s+documents?\s+only",
    r"don'?t\s+use\s+(your\s+)?(own\s+)?knowledge",
    r"strictly\s+from\s+documents?",
]

_AI_ONLY_PATTERNS = [
    r"use\s+your\s+own\s+knowledge",
    r"don'?t\s+use\s+(my\s+)?documents?",
    r"ignore\s+(my\s+)?documents?",
    r"without\s+(my\s+)?documents?",
    r"general\s+knowledge\s+only",
]


def detect_knowledge_mode(message: str, explicit_mode: Optional[str] = None) -> KnowledgeMode:
    """Detect knowledge mode from message content or explicit setting."""
    if explicit_mode:
        try:
            return KnowledgeMode(explicit_mode)
        except ValueError:
            pass

    lower = message.lower()
    for pattern in _DOCUMENTS_ONLY_PATTERNS:
        if re.search(pattern, lower):
            return KnowledgeMode.DOCUMENTS_ONLY
    for pattern in _AI_ONLY_PATTERNS:
        if re.search(pattern, lower):
            return KnowledgeMode.AI_ONLY
    return KnowledgeMode.AUTO


class HybridKnowledgeEngine:
    """
    Central decision engine for hybrid knowledge retrieval and prompt construction.
    Implements Cases 1-6 from the knowledge routing specification.
    """

    CONFIDENCE_THRESHOLD_HIGH = 0.5
    CONFIDENCE_THRESHOLD_LOW = 0.15

    def __init__(self, db: Session):
        self.db = db

    async def retrieve_and_decide(
        self,
        user_id: int,
        query: str,
        k: int = 6,
        mode: KnowledgeMode = KnowledgeMode.AUTO,
        conversation_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Execute full retrieval pipeline and determine knowledge case.

        Returns dict with:
            - case: KnowledgeCase
            - mode: KnowledgeMode
            - chunks: retrieved document chunks
            - confidence: retrieval confidence level
            - memory_context: conversation memory snippets
            - context_text: formatted context for LLM
            - system_instructions: case-specific instructions
            - metadata: debug info
        """
        t0 = time.perf_counter()
        import asyncio
        mode = detect_knowledge_mode(query, mode.value if isinstance(mode, KnowledgeMode) else mode)

        # Case 6: AI only — skip retrieval
        if mode == KnowledgeMode.AI_ONLY:
            return self._build_result(
                case=KnowledgeCase.AI_ONLY,
                mode=mode,
                chunks=[],
                confidence="none",
                memory_context=[],
                context_text="",
                elapsed_ms=int((time.perf_counter() - t0) * 1000),
                web_results=[],
            )

        user_chunks = []
        kb_chunks = []

        try:
            # Add timeout around retrieval calls (cap at 5 seconds) and run in parallel
            user_task = self._hybrid_retrieve(user_id, query, k, filters=None)
            kb_task = self._hybrid_retrieve(user_id, query, k, filters={"is_knowledge_base": True})
            
            user_chunks_res, kb_chunks_res = await asyncio.wait_for(
                asyncio.gather(user_task, kb_task, return_exceptions=True),
                timeout=5.0
            )
            
            if isinstance(user_chunks_res, Exception):
                log.warning("hybrid_knowledge.user_retrieve_failed", error=str(user_chunks_res))
            else:
                user_chunks = user_chunks_res or []
                
            if isinstance(kb_chunks_res, Exception):
                log.warning("hybrid_knowledge.kb_retrieve_failed", error=str(kb_chunks_res))
            else:
                kb_chunks = kb_chunks_res or []

        except asyncio.TimeoutError:
            log.warning("hybrid_knowledge.retrieval_timeout")
        except Exception as e:
            # Graceful fallback: do not crash if retrieval fails
            log.warning("hybrid_knowledge.retrieval_exception", error=str(e))

        # Merge and deduplicate (user docs take priority)
        seen_keys = set()
        all_chunks = []
        for chunk in user_chunks + kb_chunks:
            key = f"{chunk.get('document_id')}:{chunk.get('chunk_index')}"
            if key not in seen_keys:
                seen_keys.add(key)
                all_chunks.append(chunk)

        # Filter irrelevant and assess confidence
        all_chunks = filter_irrelevant_chunks(all_chunks, query)
        confidence = assess_retrieval_confidence(all_chunks)

        # Retrieve conversation memory
        memory_context = []
        try:
            memory_context = await self._get_memory_context(user_id, query, conversation_id)
        except Exception as e:
            log.warning("hybrid_knowledge.memory_context_failed", error=str(e))

        # Web search fallback when document confidence is low
        web_results: List[Dict[str, Any]] = []
        if (
            settings.ENABLE_WEB_SEARCH
            and mode == KnowledgeMode.AUTO
            and confidence in ("none", "low")
        ):
            try:
                web_results = await self._search_web(query)
            except Exception as e:
                log.warning("hybrid_knowledge.web_search_failed", error=str(e))

        # Determine knowledge case (graceful fallback automatically handles empty chunks as NO_DOCUMENT)
        case = self._determine_case(mode, all_chunks, confidence)

        elapsed_ms = int((time.perf_counter() - t0) * 1000)
        log.info(
            "hybrid_knowledge.decided",
            user_id=user_id,
            case=case.value,
            mode=mode.value,
            confidence=confidence,
            chunks=len(all_chunks),
            elapsed_ms=elapsed_ms,
        )

        context_text = self._format_context(all_chunks, memory_context, web_results)

        # Detailed Phase 1 Retrieval Audit Log
        doc_ids = [c.get("document_id") for c in all_chunks]
        scores = [round(c.get("score", 0.0), 3) for c in all_chunks]
        metadatas = [{k: v for k, v in c.items() if k not in ("text", "embedding")} for c in all_chunks]
        log.info(
            "retrieval.audit.details",
            chunk_count=len(all_chunks),
            similarity_scores=scores,
            retrieved_document_ids=doc_ids,
            retrieved_metadata=metadatas,
            context_length=len(context_text)
        )

        return self._build_result(
            case=case,
            mode=mode,
            chunks=all_chunks,
            confidence=confidence,
            memory_context=memory_context,
            context_text=context_text,
            elapsed_ms=elapsed_ms,
            web_results=web_results,
        )

    async def _hybrid_retrieve(
        self,
        user_id: int,
        query: str,
        k: int,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Run hybrid vector + keyword search (single pass for maximum speed)."""
        from app.rag.query_rewriter import expand_query_with_synonyms

        # Single pass: only use expanded query
        search_query = expand_query_with_synonyms(query)
        all_results: List[Dict[str, Any]] = []
        seen_keys: set = set()

        is_kb = filters and filters.get("is_knowledge_base")
        retriever_user_id = None if is_kb else user_id

        try:
            vector_results = await retrieve(
                user_id=retriever_user_id,
                query=search_query,
                k=k * 2,
                filters=filters,
                db=self.db,
            )
            
            kw_filters = dict(filters) if filters else {}
            if retriever_user_id is not None:
                kw_filters["user_id"] = retriever_user_id
            keyword_results = _keyword_search_fallback(self.db, search_query, k, kw_filters)

            if vector_results and keyword_results:
                merged = hybrid_merge(vector_results, keyword_results, search_query, top_k=k)
            else:
                merged = vector_results or keyword_results or []

            for chunk in merged:
                key = f"{chunk.get('document_id')}:{chunk.get('chunk_index')}"
                if key not in seen_keys:
                    seen_keys.add(key)
                    all_results.append(chunk)
        except Exception as e:
            log.warning("hybrid_retrieve.query_failed", query=query, error=str(e))

        # Final rerank
        from app.rag.reranker import rerank_chunks
        return rerank_chunks(all_results, query, top_k=k)

    async def _get_memory_context(
        self,
        user_id: int,
        query: str,
        conversation_id: Optional[int],
    ) -> List[str]:
        """Retrieve relevant conversation memory and learned facts."""
        memory_snippets: List[str] = []

        try:
            from app.services.memory_service import MemoryService
            facts = MemoryService(self.db).get_learned_facts(user_id)
            for fact in facts[:5]:
                memory_snippets.append(f"[memory:fact] {fact.fact}")
        except Exception as e:
            log.debug("hybrid_knowledge.memory_facts_failed", error=str(e))

        if conversation_id:
            try:
                from app.memory.short_term import get_recent
                recent = await get_recent(conversation_id, limit=4)
                for msg in recent:
                    if isinstance(msg, str) and ": " in msg:
                        role, content = msg.split(": ", 1)
                        memory_snippets.append(f"[memory:chat:{role}] {content[:300]}")
                    elif isinstance(msg, dict):
                        role = msg.get("role", "user")
                        content = msg.get("content", "")[:300]
                        if content:
                            memory_snippets.append(f"[memory:chat:{role}] {content}")
            except Exception as e:
                log.debug("hybrid_knowledge.memory_chat_failed", error=str(e))

        return memory_snippets

    async def _search_web(self, query: str) -> List[Dict[str, Any]]:
        """Fetch web search results when document retrieval is insufficient."""
        try:
            from app.services.web_search_service import WebSearchService
            service = WebSearchService()
            results = await service.search(query)
            web_chunks = []
            for i, r in enumerate(results):
                web_chunks.append({
                    "source_type": "web",
                    "title": r.title,
                    "text": r.snippet,
                    "url": r.url,
                    "score": r.score,
                    "confidence_score": min(r.score, 1.0),
                    "retrieved_at": r.retrieved_at,
                    "citation_key": f"web:{i+1}",
                })
            log.info("hybrid_knowledge.web_search", query=query, results=len(web_chunks))
            return web_chunks
        except Exception as e:
            log.debug("hybrid_knowledge.web_search_failed", error=str(e))
            return []

    def _determine_case(
        self,
        mode: KnowledgeMode,
        chunks: List[Dict[str, Any]],
        confidence: str,
    ) -> KnowledgeCase:
        if mode == KnowledgeMode.DOCUMENTS_ONLY:
            return KnowledgeCase.DOCUMENTS_ONLY
        if mode == KnowledgeMode.AI_ONLY:
            return KnowledgeCase.AI_ONLY

        if not chunks or confidence == "none":
            return KnowledgeCase.NO_DOCUMENT

        doc_ids = {c.get("document_id") for c in chunks if c.get("document_id")}
        if len(doc_ids) > 1:
            return KnowledgeCase.MULTI_DOCUMENT

        if confidence in ("high", "medium"):
            return KnowledgeCase.FULL_DOCUMENT

        return KnowledgeCase.PARTIAL_DOCUMENT

    def _format_context(
        self,
        chunks: List[Dict[str, Any]],
        memory_context: List[str],
        web_results: Optional[List[Dict[str, Any]]] = None,
    ) -> str:
        parts = []

        if memory_context:
            parts.append("=== Conversation Memory ===")
            parts.extend(memory_context)

        if chunks:
            parts.append("\n=== Document Evidence ===")
            for chunk in chunks:
                doc_id = chunk.get("document_id", "?")
                chunk_idx = chunk.get("chunk_index", "?")
                page = chunk.get("page_number")
                section = chunk.get("section")
                score = chunk.get("score", 0)
                meta_parts = [f"doc:{doc_id}#{chunk_idx}"]
                if page:
                    meta_parts.append(f"page:{page}")
                if section:
                    meta_parts.append(f"section:{section}")
                meta_parts.append(f"confidence:{score:.2f}")
                header = f"[{' | '.join(meta_parts)}]"
                parts.append(f"{header}\n{chunk.get('text', '')}")

        if web_results:
            parts.append("\n=== Web Search Results ===")
            for wr in web_results:
                key = wr.get("citation_key", "web:?")
                title = wr.get("title", "")
                url = wr.get("url", "")
                score = wr.get("score", 0)
                parts.append(
                    f"[{key} | {title} | {url} | confidence:{score:.2f}]\n{wr.get('text', '')}"
                )

        return "\n\n".join(parts)

    def _build_result(
        self,
        case: KnowledgeCase,
        mode: KnowledgeMode,
        chunks: List[Dict[str, Any]],
        confidence: str,
        memory_context: List[str],
        context_text: str,
        elapsed_ms: int,
        web_results: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        instructions = self._get_system_instructions(case, confidence)

        return {
            "case": case,
            "mode": mode,
            "chunks": chunks,
            "confidence": confidence,
            "memory_context": memory_context,
            "context_text": context_text,
            "web_results": web_results or [],
            "system_instructions": instructions,
            "metadata": {
                "retrieval_ms": elapsed_ms,
                "chunk_count": len(chunks),
                "unique_documents": len({c.get("document_id") for c in chunks}),
                "web_result_count": len(web_results or []),
                "confidence": confidence,
            },
        }

    def _get_system_instructions(self, case: KnowledgeCase, confidence: str) -> str:
        base = (
            "You are OmniAgent, an intelligent AI assistant with access to uploaded documents, "
            "a knowledge base, and conversation memory. Always be accurate and cite sources."
        )

        case_instructions = {
            KnowledgeCase.FULL_DOCUMENT: (
                "\n\nCASE: Full document match found.\n"
                "- Answer PRIMARILY from the provided document evidence.\n"
                "- Cite every claim with [doc:id#chunk] format.\n"
                "- Include page numbers and sections when available.\n"
                "- Do NOT hallucinate information not in the documents."
            ),
            KnowledgeCase.PARTIAL_DOCUMENT: (
                "\n\nCASE: Partial document match.\n"
                "- Use document evidence for what IS available.\n"
                "- Clearly separate your response into two sections:\n"
                "  ## Document Evidence\n"
                "  (facts from documents with citations)\n"
                "  ## Additional AI Explanation\n"
                "  (general knowledge to fill gaps, clearly labeled)\n"
                "- Cite documents as [doc:id#chunk]."
            ),
            KnowledgeCase.NO_DOCUMENT: (
                "\n\nCASE: No relevant documents found.\n"
                "- Answer the user's question using your general knowledge.\n"
                "- If the user's question explicitly asks about their uploaded files or documents (e.g. 'what is in my documents?', 'summarize the pdf', 'according to the files'), then explicitly state: 'This information was not found in your uploaded documents.'\n"
                "- Otherwise, just provide a direct, helpful general knowledge answer without mentioning the lack of documents.\n"
                "- Do NOT fabricate document citations."
            ),
            KnowledgeCase.MULTI_DOCUMENT: (
                "\n\nCASE: Multiple documents contain relevant information.\n"
                "- Compare evidence across all documents.\n"
                "- Merge findings and resolve any conflicts.\n"
                "- Cite ALL relevant documents as [doc:id#chunk].\n"
                "- Note any contradictions between sources."
            ),
            KnowledgeCase.DOCUMENTS_ONLY: (
                "\n\nCASE: User requested documents-only mode.\n"
                "- Use ONLY the provided document evidence.\n"
                "- Do NOT use general AI knowledge.\n"
                "- If information is not in documents, respond EXACTLY:\n"
                "  'Information not found in uploaded documents.'"
            ),
            KnowledgeCase.AI_ONLY: (
                "\n\nCASE: User requested AI knowledge only.\n"
                "- Do NOT reference or cite any documents.\n"
                "- Answer using your general knowledge.\n"
                "- Be helpful, accurate, and comprehensive."
            ),
        }

        return base + case_instructions.get(case, "")

    def build_prompt(
        self,
        query: str,
        result: Dict[str, Any],
    ) -> Tuple[str, str]:
        """
        Build the user prompt and system prompt from retrieval result.
        Returns (user_prompt, system_prompt).
        """
        case = result["case"]
        context_text = result["context_text"]
        instructions = result["system_instructions"]

        if case == KnowledgeCase.AI_ONLY:
            user_prompt = f"User Question: {query}\n\nPlease answer this question comprehensively."
            return user_prompt, instructions

        if case == KnowledgeCase.DOCUMENTS_ONLY and not result["chunks"]:
            user_prompt = (
                f"User Question: {query}\n\n"
                f"No relevant documents were found. "
                f"Respond with: 'Information not found in uploaded documents.'"
            )
            return user_prompt, instructions

        if context_text:
            user_prompt = (
                f"User Question: {query}\n\n"
                f"Available Context:\n{context_text}\n\n"
                f"Answer the question following the instructions above. "
                f"Always cite sources as [doc:id#chunk]."
            )
        else:
            user_prompt = f"User Question: {query}\n\nNo document context available."

        return user_prompt, instructions

    def enrich_citations(
        self,
        chunks: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Enrich citation chunks with document metadata from database."""
        enriched = []
        doc_cache: Dict[int, Document] = {}

        for chunk in chunks:
            doc_id = chunk.get("document_id")
            entry = dict(chunk)

            if doc_id:
                if doc_id not in doc_cache:
                    doc = self.db.exec(select(Document).where(Document.id == doc_id)).first()
                    doc_cache[doc_id] = doc
                doc = doc_cache.get(doc_id)
                if doc:
                    entry["document_name"] = doc.filename
                    entry["filename"] = doc.filename

            entry.setdefault("confidence_score", round(chunk.get("score", 0), 3))
            entry.setdefault("page_number", chunk.get("page_number"))
            entry.setdefault("section", chunk.get("section"))
            entry["snippet"] = (chunk.get("text") or "")[:240]
            enriched.append(entry)

        return enriched
