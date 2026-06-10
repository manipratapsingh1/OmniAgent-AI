import json
import time
from app.agents.state import AgentState, TraceEntry
from app.llm.ollama_client import ollama
from app.llm.prompts import TOOL_SYSTEM
from app.tools.registry import registry


async def use_tool(state: AgentState) -> AgentState:
    if "tool" not in state.route:
        return state
    t0 = time.perf_counter()
    decision = await ollama.generate(prompt=state.query, model=state.model, system=TOOL_SYSTEM)
    try:
        obj = json.loads(decision)
        name = obj.get("tool", "none")
        args = obj.get("args", {})
    except Exception:
        name, args = "none", {}

    if name == "none" or name not in registry.names():
        state.trace.append(TraceEntry(agent="tool", input=state.query, output="no tool used",
                                      latency_ms=int((time.perf_counter() - t0) * 1000)))
        return state

    try:
        result = await registry.run(name, args)
        state.tool_result = f"[{name}] {result}"
    except Exception as e:
        state.tool_result = f"[{name}] error: {e}"

    state.trace.append(TraceEntry(agent="tool", input=json.dumps({"tool": name, "args": args}),
                                  output=state.tool_result or "", latency_ms=int((time.perf_counter() - t0) * 1000)))
    return state