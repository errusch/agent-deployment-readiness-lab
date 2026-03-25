from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class RequestThreadMessage(BaseModel):
    sender: str = Field(alias="from")
    timestamp: str
    body: str

    model_config = ConfigDict(populate_by_name=True)


class RequestPacket(BaseModel):
    request_id: str
    workflow_type: str
    subject: str
    thread: list[RequestThreadMessage] = Field(default_factory=list)
    metadata: dict[str, str | int | float | bool | None] = Field(default_factory=dict)


class RequiredFieldDefinition(BaseModel):
    name: str
    description: str
    required: bool = True


class ValidationSchema(BaseModel):
    workflow_type: str
    required_fields: list[RequiredFieldDefinition] = Field(default_factory=list)


class FieldValidationResult(BaseModel):
    name: str
    description: str
    required: bool
    present: bool
    value: str | None = None
    evidence_snippets: list[str] = Field(default_factory=list)


class ValidationReport(BaseModel):
    workflow_type: str
    readiness_verdict: Literal["ready_for_draft", "needs_context"]
    present_fields: list[str] = Field(default_factory=list)
    missing_required_fields: list[str] = Field(default_factory=list)
    field_results: list[FieldValidationResult] = Field(default_factory=list)
    summary: str


class StructuredBrief(BaseModel):
    problem_statement: str = Field(description="The workflow problem to solve.")
    target_users: list[str] = Field(default_factory=list)
    current_process: list[str] = Field(default_factory=list)
    desired_outcomes: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)


class WorkflowAnalysis(BaseModel):
    workflow_type: Literal[
        "onboarding_ops",
        "executive_support",
        "support_handoff",
        "research_workflow",
        "general_ops",
    ] = "general_ops"
    reasoning_summary: str
    automation_opportunities: list[str] = Field(default_factory=list)
    required_capabilities: list[str] = Field(default_factory=list)
    human_review_points: list[str] = Field(default_factory=list)
    likely_failure_modes: list[str] = Field(default_factory=list)
    business_risks: list[str] = Field(default_factory=list)
    recommended_tools: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)


class IntakeAnalysis(BaseModel):
    structured_brief: StructuredBrief
    workflow_analysis: WorkflowAnalysis


class DraftPlan(BaseModel):
    title: str
    executive_summary: str
    agent_goal: str
    graph_nodes: list[str] = Field(default_factory=list)
    tool_plan: list[str] = Field(default_factory=list)
    guardrails: list[str] = Field(default_factory=list)
    rollout_checklist: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    approval_prompt: str
    confidence: float = Field(ge=0.0, le=1.0)
