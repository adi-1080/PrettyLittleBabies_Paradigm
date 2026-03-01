"""
graph.py — LangGraph Workflow Definition

  START → Historian → Strategist → Orchestrator → END
"""

from langgraph.graph import StateGraph, START, END

from state import AgentState
from agents.historian import historian_node
from agents.strategist import strategist_node
from agents.orchestrator import orchestrator_node


def build_graph() -> StateGraph:
    workflow = StateGraph(AgentState)

    workflow.add_node("historian", historian_node)
    workflow.add_node("strategist", strategist_node)
    workflow.add_node("orchestrator", orchestrator_node)

    workflow.add_edge(START, "historian")
    workflow.add_edge("historian", "strategist")
    workflow.add_edge("strategist", "orchestrator")
    workflow.add_edge("orchestrator", END)

    return workflow.compile()


app = build_graph()
