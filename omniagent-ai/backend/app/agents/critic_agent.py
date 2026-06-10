import time
from app.agents.state import AgentState, TraceEntry
from app.llm.ollama_client import ollama
from app.llm.prompts import CRITIC_SYSTEM


async def critique(state: AgentState) -> AgentState:
    if "critic" not in state.route or not state.final:
        return state
    t0 = time.perf_counter()
    out = await ollama.generate(prompt=state.final, model=state.model, system=CRITIC_SYSTEM)
    state.final = out
    state.trace.append(TraceEntry(agent="critic", input="polish", output=out,
                                  latency_ms=int((time.perf_counter() - t0) * 1000)))
    return state