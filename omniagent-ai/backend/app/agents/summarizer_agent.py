import time
from app.agents.state import AgentState, TraceEntry
from app.llm.ollama_client import ollama
from app.llm.prompts import SUMMARIZER_SYSTEM


async def summarize(state: AgentState) -> AgentState:
    if "summarizer" not in state.route or not state.final:
        return state
    if len(state.final) < 1200:
        return state
    t0 = time.perf_counter()
    out = await ollama.generate(prompt=state.final, model=state.model, system=SUMMARIZER_SYSTEM)
    state.final = out
    state.trace.append(TraceEntry(agent="summarizer", input="compress", output=out,
                                  latency_ms=int((time.perf_counter() - t0) * 1000)))
    return state