"""Deep Research Mode — multi-source research with evidence ranking and report generation."""
from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import structlog
from sqlmodel import Session

from app.config import get_settings
from app.services.ai.hybrid_knowledge_engine import HybridKnowledgeEngine, KnowledgeMode
from app.services.ai.model_router import ModelRouter, TaskType
from app.services.ai.ollama_provider import OllamaProvider
from app.services.web_search_service import WebSearchService
from app.utils.citations import validate_citation_accuracy

log = structlog.get_logger("deep_research")
settings = get_settings()

RESEARCH_SYSTEM = """You are a Deep Research Agent. Produce thorough, evidence-based reports.

Rules:
- Cite ALL sources: [doc:id#chunk] for documents, [web:N] for web results
- Separate facts from inference
- Flag contradictions between sources
- Include an Executive Summary at the top
- End with a References section listing all cited sources
- Never present unsupported claims as facts"""


class DeepResearchService:
    """Multi-source research agent combining documents, web, and AI reasoning."""

    def __init__(self, db: Session, providers: Optional[dict] = None):
        self.db = db
        self.knowledge_engine = HybridKnowledgeEngine(db)
        self.web_search = WebSearchService()
        _providers = providers or {"ollama": OllamaProvider()}
        self.router = ModelRouter(_providers)

    async def research(
        self,
        user_id: int,
        query: str,
        include_web: bool = True,
        conversation_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        t0 = time.perf_counter()

        # Document + memory retrieval
        knowledge = await self.knowledge_engine.retrieve_and_decide(
            user_id=user_id,
            query=query,
            k=8,
            mode=KnowledgeMode.AUTO,
            conversation_id=conversation_id,
        )

        web_results = []
        if include_web and settings.ENABLE_WEB_SEARCH:
            web_results = await self.web_search.search(query)
        elif include_web:
            # Force web even if hybrid engine didn't trigger it
            try:
                web_results = await self.web_search.search(query)
            except Exception as e:
                log.debug("deep_research.web_skipped", error=str(e))

        # Build evidence context
        evidence_parts = []
        if knowledge["context_text"]:
            evidence_parts.append(knowledge["context_text"])

        if web_results and not knowledge.get("web_results"):
            evidence_parts.append("\n=== Web Search Results ===")
            for i, r in enumerate(web_results):
                evidence_parts.append(
                    f"[web:{i+1} | {r.title} | {r.url} | confidence:{r.score:.2f}]\n{r.snippet}"
                )

        context = "\n\n".join(evidence_parts) or "(no external evidence found)"

        prompt = f"""Research Question: {query}

Available Evidence:
{context}

Produce a comprehensive research report with:
1. Executive Summary (3-5 sentences)
2. Key Findings (with citations)
3. Analysis and Synthesis
4. Contradictions or Gaps (if any)
5. References (all sources cited)

Use [doc:id#chunk] for documents and [web:N] for web sources."""

        report, provider_used = await self.router.generate(
            prompt=prompt,
            query=query,
            task_type=TaskType.RESEARCH.value,
            system=RESEARCH_SYSTEM,
            model=settings.OLLAMA_FAST_MODEL,
        )

        all_sources = list(knowledge.get("chunks", []))
        for i, wr in enumerate(web_results):
            all_sources.append({
                "source_type": "web",
                "title": wr.title,
                "url": wr.url,
                "text": wr.snippet,
                "score": wr.score,
                "citation_key": f"web:{i+1}",
            })

        citation_stats = validate_citation_accuracy(report, all_sources)
        elapsed_ms = int((time.perf_counter() - t0) * 1000)

        log.info(
            "deep_research.complete",
            user_id=user_id,
            elapsed_ms=elapsed_ms,
            provider=provider_used,
            doc_chunks=len(knowledge.get("chunks", [])),
            web_results=len(web_results),
        )

        return {
            "query": query,
            "report": report,
            "executive_summary": self._extract_summary(report),
            "sources": {
                "documents": knowledge.get("chunks", []),
                "web": [r.to_dict() for r in web_results],
            },
            "citation_accuracy": citation_stats,
            "knowledge_case": knowledge["case"].value,
            "confidence": knowledge["confidence"],
            "provider_used": provider_used,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "elapsed_ms": elapsed_ms,
        }

    def _extract_summary(self, report: str) -> str:
        """Extract executive summary section from report."""
        lower = report.lower()
        markers = ["executive summary", "## summary", "# summary"]
        for marker in markers:
            idx = lower.find(marker)
            if idx >= 0:
                rest = report[idx + len(marker):].strip().lstrip(":\n#")
                # Take until next major section
                end = rest.find("\n## ")
                if end > 0:
                    return rest[:end].strip()
                return rest[:500].strip()
        return report[:400].strip()
