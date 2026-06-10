import time
from app.agents.state import AgentState, TraceEntry
from app.llm.ollama_client import ollama
from app.llm.prompts import PLANNER_SYSTEM


async def plan(state: AgentState) -> AgentState:
    if "planner" not in state.route:
        return state
    t0 = time.perf_counter()
    out = await ollama.generate(prompt=state.query, model=state.model, system=PLANNER_SYSTEM)
    state.plan = out
    state.trace.append(TraceEntry(agent="planner", input=state.query, output=out,
                                  latency_ms=int((time.perf_counter() - t0) * 1000)))
    return state