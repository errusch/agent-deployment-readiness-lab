from __future__ import annotations

from functools import lru_cache
from typing import Literal

from langchain.chat_models import init_chat_model
from langchain.messages import HumanMessage, SystemMessage
from langgraph.types import interrupt

from .config import get_settings
from .demo_mode import demo_draft_plan, demo_structured_brief, demo_workflow_analysis
from .prompts import ANALYZE_SYSTEM_PROMPT, DRAFT_PLAN_SYSTEM_PROMPT, INGEST_SYSTEM_PROMPT
from .schemas import DraftPlan, StructuredBrief, WorkflowAnalysis
from .state import GraphState


@lru_cache(maxsize=1)
def get_model():
    settings = get_settings()
    kwargs = {"temperature": 0}
    if settings.reasoning_effort:
        kwargs["reasoning_effort"] = settings.reasoning_effort
    return init_chat_model(settings.model_name, **kwargs)


REFERENCE_PATTERN_LIBRARY: dict[str, list[str]] = {
    "onboarding_ops": [
        "Use a first-pass intake step to normalize inputs and identify missing information early.",
        "Insert a human approval point before any external-facing handoff or customer communication.",
        "Track missing requirements explicitly so the agent can escalate instead of improvising.",
    ],
    "executive_support": [
        "Favor concise summaries, explicit next actions, and clear ownership boundaries.",
        "Require approval before sending or finalizing anything that could be interpreted as executive intent.",
        "Use a checklist for recurring handoffs so the workflow stays reliable over time.",
    ],
    "support_handoff": [
        "Separate triage, evidence gathering, and final handoff steps.",
        "Escalate when evidence is thin instead of confidently inventing resolution paths.",
        "Add review gates for priority, risk, and customer-facing wording.",
    ],
    "research_workflow": [
        "Document sources gathered, confidence in evidence, and unresolved questions.",
        "Use reflection or review before final synthesis when stakes are high.",
        "Keep final outputs structured so humans can validate quickly.",
    ],
    "general_ops": [
        "Normalize the request, identify dependencies, and make uncertainty visible.",
        "Add a clear approval checkpoint before irreversible actions.",
        "Use rollout checklists to move from draft logic to operational usage.",
    ],
}


def _structured_invoke(schema, system_prompt: str, user_prompt: str):
    model = get_model().with_structured_output(schema)
    return model.invoke(
        [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]
    )


def _load_structured_brief(payload: dict | StructuredBrief) -> StructuredBrief:
    if isinstance(payload, StructuredBrief):
        return payload
    return StructuredBrief.model_validate(payload)


def _load_workflow_analysis(payload: dict | WorkflowAnalysis) -> WorkflowAnalysis:
    if isinstance(payload, WorkflowAnalysis):
        return payload
    return WorkflowAnalysis.model_validate(payload)


def _load_draft_plan(payload: dict | DraftPlan) -> DraftPlan:
    if isinstance(payload, DraftPlan):
        return payload
    return DraftPlan.model_validate(payload)


def _format_brief_for_llm(state: GraphState) -> str:
    return f"""Original brief:
{state["brief"]}

Return a structured planning brief.
"""


def _format_analysis_input(structured_brief: StructuredBrief) -> str:
    return f"""Structured brief:
{structured_brief.model_dump_json(indent=2)}

Analyze this workflow for agent deployment readiness.
"""


def _format_plan_input(
    structured_brief: StructuredBrief,
    workflow_analysis: WorkflowAnalysis,
    reference_patterns: list[str],
) -> str:
    patterns_block = "\n".join(f"- {pattern}" for pattern in reference_patterns)
    return f"""Structured brief:
{structured_brief.model_dump_json(indent=2)}

Workflow analysis:
{workflow_analysis.model_dump_json(indent=2)}

Reference patterns:
{patterns_block}

Produce a scoped first-pass deployment plan.
"""


def get_reference_patterns(workflow_type: str) -> list[str]:
    return REFERENCE_PATTERN_LIBRARY.get(
        workflow_type,
        REFERENCE_PATTERN_LIBRARY["general_ops"],
    )


def parse_reviewer_response(response: object) -> tuple[str, str]:
    if isinstance(response, bool):
        return ("approve" if response else "revise", "")

    if isinstance(response, str):
        lowered = response.strip().lower()
        if lowered in {"approve", "approved", "yes", "y"}:
            return ("approve", "")
        return ("revise", response.strip())

    if isinstance(response, dict):
        approved = response.get("approved")
        notes = str(response.get("notes", "")).strip()
        action = str(response.get("action", "")).strip().lower()
        if action in {"approve", "approved"} or approved is True:
            return ("approve", notes)
        return ("revise", notes)

    return ("revise", "")


def render_final_output(state: GraphState) -> str:
    structured_brief = _load_structured_brief(state["structured_brief"])
    workflow_analysis = _load_workflow_analysis(state["workflow_analysis"])
    draft_plan = _load_draft_plan(state["draft_plan"])
    reviewer_notes = state.get("reviewer_notes", "").strip()

    lines = [
        f"# {draft_plan.title}",
        "",
        "## Workflow Summary",
        structured_brief.problem_statement,
        "",
        "## Recommended Agent Goal",
        draft_plan.agent_goal,
        "",
        "## Proposed Graph Nodes",
    ]
    lines.extend(f"- {node}" for node in draft_plan.graph_nodes)
    lines.extend(
        [
            "",
            "## Tool Plan",
        ]
    )
    lines.extend(f"- {tool}" for tool in draft_plan.tool_plan)
    lines.extend(
        [
            "",
            "## Human Review Points",
        ]
    )
    lines.extend(f"- {item}" for item in workflow_analysis.human_review_points)
    lines.extend(
        [
            "",
            "## Likely Failure Modes",
        ]
    )
    lines.extend(f"- {item}" for item in workflow_analysis.likely_failure_modes)
    lines.extend(
        [
            "",
            "## Guardrails",
        ]
    )
    lines.extend(f"- {item}" for item in draft_plan.guardrails)
    lines.extend(
        [
            "",
            "## Rollout Checklist",
        ]
    )
    lines.extend(f"- {item}" for item in draft_plan.rollout_checklist)
    lines.extend(
        [
            "",
            "## Confidence",
            f"{draft_plan.confidence:.2f}",
        ]
    )
    if reviewer_notes:
        lines.extend(
            [
                "",
                "## Reviewer Notes",
                reviewer_notes,
            ]
        )
    lines.extend(
        [
            "",
            "## Limitations",
        ]
    )
    lines.extend(f"- {item}" for item in draft_plan.limitations)
    return "\n".join(lines)


def render_escalation_output(state: GraphState) -> str:
    structured_brief = _load_structured_brief(state["structured_brief"])
    workflow_analysis = _load_workflow_analysis(state["workflow_analysis"])
    draft_plan = _load_draft_plan(state["draft_plan"])
    reviewer_notes = state.get("reviewer_notes", "").strip()

    lines = [
        "# Additional Context Needed",
        "",
        "The workflow can be planned, but the current brief is not strong enough to recommend rollout without more detail.",
        "",
        "## Missing Information",
    ]
    lines.extend(f"- {item}" for item in structured_brief.missing_information)
    lines.extend(
        [
            "",
            "## Key Risks",
        ]
    )
    lines.extend(f"- {item}" for item in workflow_analysis.business_risks)
    lines.extend(
        [
            "",
            "## Conservative Next Step",
            "Run a narrower pilot after clarifying ownership, tool access, and approval boundaries.",
            "",
            "## Confidence",
            f"{draft_plan.confidence:.2f}",
        ]
    )
    if reviewer_notes:
        lines.extend(
            [
                "",
                "## Reviewer Notes",
                reviewer_notes,
            ]
        )
    return "\n".join(lines)


def ingest_brief(state: GraphState) -> GraphState:
    if get_settings().demo_mode:
        return {"structured_brief": demo_structured_brief(state["brief"]).model_dump()}

    structured_brief = _structured_invoke(
        StructuredBrief,
        INGEST_SYSTEM_PROMPT,
        _format_brief_for_llm(state),
    )
    return {"structured_brief": structured_brief.model_dump()}


def analyze_workflow(state: GraphState) -> GraphState:
    structured_brief = _load_structured_brief(state["structured_brief"])
    if get_settings().demo_mode:
        workflow_analysis = demo_workflow_analysis(structured_brief, state["brief"])
        reference_patterns = get_reference_patterns(workflow_analysis.workflow_type)
        return {
            "workflow_analysis": workflow_analysis.model_dump(),
            "reference_patterns": reference_patterns,
        }

    workflow_analysis = _structured_invoke(
        WorkflowAnalysis,
        ANALYZE_SYSTEM_PROMPT,
        _format_analysis_input(structured_brief),
    )
    reference_patterns = get_reference_patterns(workflow_analysis.workflow_type)
    return {
        "workflow_analysis": workflow_analysis.model_dump(),
        "reference_patterns": reference_patterns,
    }


def draft_plan(state: GraphState) -> GraphState:
    structured_brief = _load_structured_brief(state["structured_brief"])
    workflow_analysis = _load_workflow_analysis(state["workflow_analysis"])
    reference_patterns = state["reference_patterns"]
    if get_settings().demo_mode:
        return {
            "draft_plan": demo_draft_plan(
                structured_brief,
                workflow_analysis,
                reference_patterns,
            ).model_dump()
        }

    draft = _structured_invoke(
        DraftPlan,
        DRAFT_PLAN_SYSTEM_PROMPT,
        _format_plan_input(structured_brief, workflow_analysis, reference_patterns),
    )
    return {"draft_plan": draft.model_dump()}


def review_gate(state: GraphState) -> GraphState:
    draft = _load_draft_plan(state["draft_plan"])
    workflow_analysis = _load_workflow_analysis(state["workflow_analysis"])
    response = interrupt(
        {
            "title": "Review proposed deployment plan",
            "summary": draft.executive_summary,
            "confidence": draft.confidence,
            "approval_prompt": draft.approval_prompt,
            "recommended_action": "approve"
            if draft.confidence >= get_settings().approval_confidence_threshold
            else "revise",
            "likely_failure_modes": workflow_analysis.likely_failure_modes,
            "human_review_points": workflow_analysis.human_review_points,
            "instructions": "Reply with {'approved': true, 'notes': '...'} to continue, or send revision notes to escalate.",
        }
    )
    decision, notes = parse_reviewer_response(response)
    return {
        "reviewer_decision": decision,
        "reviewer_notes": notes,
    }


def route_after_review(state: GraphState) -> Literal["finalize_plan", "escalate_request"]:
    draft = _load_draft_plan(state["draft_plan"])
    threshold = get_settings().approval_confidence_threshold
    if state.get("reviewer_decision") == "approve" and draft.confidence >= threshold:
        return "finalize_plan"
    return "escalate_request"


def finalize_plan(state: GraphState) -> GraphState:
    return {"final_output": render_final_output(state)}


def escalate_request(state: GraphState) -> GraphState:
    return {"final_output": render_escalation_output(state)}
