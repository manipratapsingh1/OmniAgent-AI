import time
from app.agents.state import AgentState, TraceEntry
from app.llm.ollama_client import ollama
from app.llm.prompts import VERIFIER_SYSTEM


async def verify(state: AgentState) -> AgentState:
    if "verifier" not in state.route or not state.draft:
        state.final = state.draft or state.tool_result or "No answer generated."
        return state
    
    t0 = time.perf_counter()
    
    # AI Guardrail: Faithfulness Check
    # Cross-reference draft with context
    context_str = "\n".join([c.snippet for c in state.context]) if state.context else "No context."
    
    faithfulness_prompt = f"""You are a Fact-Checker. Check if the draft answer is supported by the context.
    If the draft answer contains facts NOT in the context, remove or correct them.
    
    CONTEXT:
    {context_str[:2000]}
    
    DRAFT ANSWER:
    {state.draft}
    
    Return the corrected final answer that is 100% faithful to the context."""

    out = await ollama.generate(prompt=faithfulness_prompt, model=state.model, system=VERIFIER_SYSTEM)
    state.final = out
    state.trace.append(TraceEntry(agent="verifier", input=state.draft[:500], output=out[:500],
                                  latency_ms=int((time.perf_counter() - t0) * 1000)))
    return state