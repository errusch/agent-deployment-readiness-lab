from __future__ import annotations

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from .nodes import (
    draft_plan,
    escalate_request,
    finalize_plan,
    ingest_and_analyze_workflow,
    review_gate,
    route_after_review,
)
from .state import GraphState


def build_graph():
    builder = StateGraph(GraphState)
    builder.add_node("ingest_and_analyze_workflow", ingest_and_analyze_workflow)
    builder.add_node("draft_plan", draft_plan)
    builder.add_node("review_gate", review_gate)
    builder.add_node("finalize_plan", finalize_plan)
    builder.add_node("escalate_request", escalate_request)

    builder.add_edge(START, "ingest_and_analyze_workflow")
    builder.add_edge("ingest_and_analyze_workflow", "draft_plan")
    builder.add_edge("draft_plan", "review_gate")
    builder.add_conditional_edges(
        "review_gate",
        route_after_review,
        ["finalize_plan", "escalate_request"],
    )
    builder.add_edge("finalize_plan", END)
    builder.add_edge("escalate_request", END)

    return builder.compile(checkpointer=MemorySaver())


graph = build_graph()
