"""
graph.py — LangGraph Workflow Definition

Defines the StateGraph with three sequential nodes:
  START → Historian → Strategist → Orchestrator → END

The AgentState is passed and updated between each node.
"""

from langgraph.graph import StateGraph, START, END

from state import AgentState
from agents.historian import historian_node
from agents.strategist import strategist_node
from agents.orchestrator import orchestrator_node


def build_graph() -> StateGraph:
    """
    Constructs and compiles the Social Autopilot LangGraph workflow.

    Returns:
        A compiled LangGraph application ready to invoke.
    """
    workflow = StateGraph(AgentState)

    # ── Register nodes ────────────────────────────────────────────────────
    workflow.add_node("historian", historian_node)
    workflow.add_node("strategist", strategist_node)
    workflow.add_node("orchestrator", orchestrator_node)

    # ── Define edges (linear chain) ───────────────────────────────────────
    workflow.add_edge(START, "historian")
    workflow.add_edge("historian", "strategist")
    workflow.add_edge("strategist", "orchestrator")
    workflow.add_edge("orchestrator", END)

    return workflow.compile()


# Pre-compiled graph instance for easy import
app = build_graph()
