import time
import structlog
from app.agents.state import AgentState, TraceEntry
from app.rag.retriever import retrieve
from app.services.ai.provider_registry import get_model_router
from app.llm.prompts import RESEARCH_SYSTEM
from app.utils.citations import validate_citation_accuracy
from app.config import get_settings

log = structlog.get_logger("research_agent")
settings = get_settings()


async def research(state: AgentState) -> AgentState:
    if "research" not in state.route:
        return state

    t0 = time.perf_counter()
    router = get_model_router()
    context_parts = []

    if state.use_rag:
        ctx = await retrieve(user_id=state.user_id, query=state.query, k=4)
        state.context = ctx

        if ctx:
            context_parts.append("\n\n".join(
                [f"[doc:{c['document_id']}#{c['chunk_index']}] {c['text']}" for c in ctx]
            ))
            log.info("research.context_retrieved", chunks=len(ctx))
        else:
            log.warning("research.no_context_found", query=state.query)

    if settings.ENABLE_WEB_SEARCH and (not state.context or len(state.context) < 2):
        try:
            from app.services.web_search_service import WebSearchService
            web_results = await WebSearchService().search(state.query)
            if web_results:
                web_text = "\n\n".join(
                    f"[web:{i+1} | {r.title} | {r.url}]\n{r.snippet}"
                    for i, r in enumerate(web_results)
                )
                context_parts.append(f"=== Web Results ===\n{web_text}")
                for i, r in enumerate(web_results):
                    state.context.append({
                        "source_type": "web",
                        "title": r.title,
                        "url": r.url,
                        "text": r.snippet,
                        "citation_key": f"web:{i+1}",
                    })
        except Exception as e:
            log.debug("research.web_search_failed", error=str(e))

    context_text = "\n\n".join(context_parts) if context_parts else "(no relevant context found)"

    prompt = f"""User question: {state.query}

Context from documents and web:
{context_text}

Please provide a thorough, accurate answer based on the context. Cite sources using [doc:id#chunk] or [web:N] format."""

    out, provider_used = await router.generate(
        prompt=prompt,
        query=state.query,
        task_type="research",
        model=state.model,
        system=RESEARCH_SYSTEM,
    )
    state.draft = out

    citation_stats = validate_citation_accuracy(out, state.context)
    log.info(
        "research.citations_validated",
        provider=provider_used,
        citations_found=citation_stats["citations_in_text"],
        verified_sources=citation_stats["verified_sources"],
        accuracy_score=citation_stats["accuracy_score"],
    )

    state.trace.append(TraceEntry(
        agent="research",
        input=state.query,
        output=out,
        latency_ms=int((time.perf_counter() - t0) * 1000),
    ))
    return state
