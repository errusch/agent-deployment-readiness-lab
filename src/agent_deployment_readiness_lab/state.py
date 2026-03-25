from __future__ import annotations

from typing import NotRequired, TypedDict

class GraphState(TypedDict):
    brief: str
    structured_brief: NotRequired[dict]
    workflow_analysis: NotRequired[dict]
    draft_plan: NotRequired[dict]
    reference_patterns: NotRequired[list[str]]
    reviewer_decision: NotRequired[str]
    reviewer_notes: NotRequired[str]
    final_output: NotRequired[str]
