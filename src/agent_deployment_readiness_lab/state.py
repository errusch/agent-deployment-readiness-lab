from __future__ import annotations

from typing import NotRequired, TypedDict

class GraphState(TypedDict):
    brief: str
    source_mode: NotRequired[str]
    request_file: NotRequired[str]
    schema_file: NotRequired[str]
    request_packet: NotRequired[dict]
    validation_schema: NotRequired[dict]
    validation_report: NotRequired[dict]
    structured_brief: NotRequired[dict]
    workflow_analysis: NotRequired[dict]
    draft_plan: NotRequired[dict]
    reference_patterns: NotRequired[list[str]]
    reviewer_decision: NotRequired[str]
    reviewer_notes: NotRequired[str]
    final_output: NotRequired[str]
