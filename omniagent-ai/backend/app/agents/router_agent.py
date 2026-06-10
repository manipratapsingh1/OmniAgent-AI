import time
from app.agents.state import AgentState, TraceEntry
from app.llm.ollama_client import ollama
from app.llm.prompts import ROUTER_SYSTEM


async def route(state: AgentState) -> AgentState:
    t0 = time.perf_counter()
    out = await ollama.generate(prompt=state.query, model=state.model, system=ROUTER_SYSTEM)
    agents = [a.strip().lower() for a in out.split(",") if a.strip()]
    valid = {"planner", "research", "tool", "memory", "summarizer", "verifier", "critic"}
    selected = [a for a in agents if a in valid] or ["planner", "research", "verifier"]
    state.route = selected
    state.trace.append(
        TraceEntry(agent="router", input=state.query, output=",".join(selected),
                   latency_ms=int((time.perf_counter() - t0) * 1000))
    )
    return state