from langgraph.graph import StateGraph, END

from app.agents.state import AgentState
from app.agents.router_agent import route
from app.agents.memory_agent import attach_memory
from app.agents.planner_agent import plan
from app.agents.research_agent import research
from app.agents.tool_agent import use_tool
from app.agents.verifier_agent import verify
from app.agents.critic_agent import critique
from app.agents.summarizer_agent import summarize


def build_graph():
    g = StateGraph(AgentState)
    g.add_node("router", route)
    g.add_node("memory", attach_memory)
    g.add_node("planner", plan)
    g.add_node("research", research)
    g.add_node("tool", use_tool)
    g.add_node("verifier", verify)
    g.add_node("critic", critique)
    g.add_node("summarizer", summarize)

    g.set_entry_point("router")
    g.add_edge("router", "memory")
    g.add_edge("memory", "planner")
    
    # Parallelize research and tool (both independent after planner)
    g.add_edge("planner", "research")
    g.add_edge("planner", "tool")
    
    # Both converge to verifier
    g.add_edge("research", "verifier")
    g.add_edge("tool", "verifier")
    
    # Sequential after verifier
    g.add_edge("verifier", "critic")
    g.add_edge("critic", "summarizer")
    g.add_edge("summarizer", END)
    return g.compile()


GRAPH = build_graph()