import time
import structlog
from app.agents.state import AgentState, TraceEntry
from app.rag.retriever import retrieve
from app.llm.ollama_client import ollama
from app.llm.prompts import RESEARCH_SYSTEM
from app.utils.citations import get_citations_with_fallback, validate_citation_accuracy

log = structlog.get_logger("research_agent")


async def research(state: AgentState) -> AgentState:
    if "research" not in state.route:
        return state
    
    t0 = time.perf_counter()
    
    if state.use_rag:
        ctx = await retrieve(user_id=state.user_id, query=state.query, k=4)
        state.context = ctx
        
        if ctx:
            context_text = "\n\n".join(
                [f"[doc:{c['document_id']}#{c['chunk_index']}] {c['text']}" for c in ctx]
            )
            log.info("research.context_retrieved", chunks=len(ctx))
        else:
            context_text = "(no relevant context found)"
            log.warning("research.no_context_found", query=state.query)
    else:
        context_text = "(RAG disabled)"

    prompt = f"""User question: {state.query}

Context from documents:
{context_text}

Please provide a thorough, accurate answer based on the context. Remember to cite sources using [doc:id#chunk] format."""
    
    out = await ollama.generate(prompt=prompt, model=state.model, system=RESEARCH_SYSTEM)
    state.draft = out
    
    # Validate citations in research output
    citation_stats = validate_citation_accuracy(out, state.context)
    log.info(
        "research.citations_validated",
        citations_found=citation_stats["citations_in_text"],
        verified_sources=citation_stats["verified_sources"],
        accuracy_score=citation_stats["accuracy_score"],
    )
    
    state.trace.append(TraceEntry(
        agent="research",
        input=state.query,
        output=out,
        latency_ms=int((time.perf_counter() - t0) * 1000)
    ))
    return state