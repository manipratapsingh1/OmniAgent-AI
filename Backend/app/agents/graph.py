# backend/app/agents/graph.py
from .state import AgentState
from langgraph.graph import StateGraph, START, END
from.nodes import planner, executor, verifier

def router(state: AgentState):
    """Deterministic routing logic """
    last_res = state["step_results"][-1]
    if last_res.score >= 0.85:
        if state["current_step_idx"] >= len(state["plan"]) - 1:
            return "end"
        return "next_step"
    return "retry"

builder = StateGraph(AgentState)
builder.add_node("planner", planner)
builder.add_node("executor", executor)
builder.add_node("verifier", verifier)

builder.add_edge(START, "planner")
builder.add_edge("planner", "executor")
builder.add_edge("executor", "verifier")
builder.add_conditional_edges(
    "verifier", 
    router, 
    {"next_step": "executor", "retry": "executor", "end": END}
)
agent_app = builder.compile()