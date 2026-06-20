from __future__ import annotations

from functools import lru_cache

from langgraph.graph import END, START, StateGraph

from app.xninetzy.agent.executor import agent_node
from app.xninetzy.agent.orchestrator import orchestrator_node, route_from_orchestrator
from app.xninetzy.agent.response import clarify_node, direct_node, format_node
from app.xninetzy.agent.state import AgentState


def build_graph() -> StateGraph:
    builder = StateGraph(AgentState)

    builder.add_node("orchestrator", orchestrator_node)
    builder.add_node("agent", agent_node)
    builder.add_node("direct", direct_node)
    builder.add_node("clarify", clarify_node)
    builder.add_node("format", format_node)

    builder.add_edge(START, "orchestrator")

    builder.add_conditional_edges(
        "orchestrator",
        route_from_orchestrator,
        {
            "agent": "agent",
            "direct": "direct",
            "clarify": "clarify",
        },
    )

    builder.add_edge("agent", "format")
    builder.add_edge("direct", "format")
    builder.add_edge("clarify", "format")
    builder.add_edge("format", END)

    return builder


@lru_cache(maxsize=1)
def get_compiled_graph():
    return build_graph().compile()
