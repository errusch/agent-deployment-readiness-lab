from __future__ import annotations

from typing import NotRequired, TypedDict

from .schemas import DraftPlan, StructuredBrief, WorkflowAnalysis


class GraphState(TypedDict):
    brief: str
    structured_brief: NotRequired[StructuredBrief]
    workflow_analysis: NotRequired[WorkflowAnalysis]
    draft_plan: NotRequired[DraftPlan]
    reference_patterns: NotRequired[list[str]]
    reviewer_decision: NotRequired[str]
    reviewer_notes: NotRequired[str]
    final_output: NotRequired[str]

