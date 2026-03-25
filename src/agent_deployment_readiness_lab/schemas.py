from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


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

