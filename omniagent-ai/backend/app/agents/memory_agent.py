import time
from app.agents.state import AgentState, TraceEntry
from app.memory.short_term import get_recent
from app.memory.long_term import recall


async def attach_memory(state: AgentState) -> AgentState:
    if "memory" not in state.route:
        return state
    t0 = time.perf_counter()
    recent = await get_recent(state.conversation_id, limit=6)
    long = await recall(state.user_id, state.query, k=3)
    blob = "Recent:\n" + "\n".join(recent) + "\n\nLong-term:\n" + "\n".join(long)
    # Memory is appended to query context for downstream agents
    state.query = f"{state.query}\n\n[memory]\n{blob}"
    state.trace.append(TraceEntry(agent="memory", input="recall", output=blob[:400],
                                  latency_ms=int((time.perf_counter() - t0) * 1000)))
    return state