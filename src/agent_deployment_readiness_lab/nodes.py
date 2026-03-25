from __future__ import annotations

from functools import lru_cache
from typing import Literal

from langchain.chat_models import init_chat_model
from langchain.messages import HumanMessage, SystemMessage
from langgraph.types import interrupt

from .config import get_settings
from .demo_mode import demo_draft_plan, demo_structured_brief, demo_workflow_analysis
from .intake_adapter import (
    build_brief_from_request,
    load_request_packet,
    load_validation_schema,
    validate_request_packet,
)
from .prompts import DRAFT_PLAN_SYSTEM_PROMPT, INGEST_AND_ANALYZE_SYSTEM_PROMPT
from .schemas import (
    DraftPlan,
    IntakeAnalysis,
    RequestPacket,
    StructuredBrief,
    ValidationReport,
    ValidationSchema,
    WorkflowAnalysis,
)
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


def _load_request_packet(payload: dict | RequestPacket) -> RequestPacket:
    if isinstance(payload, RequestPacket):
        return payload
    return RequestPacket.model_validate(payload)


def _load_validation_schema(payload: dict | ValidationSchema) -> ValidationSchema:
    if isinstance(payload, ValidationSchema):
        return payload
    return ValidationSchema.model_validate(payload)


def _load_validation_report(payload: dict | ValidationReport) -> ValidationReport:
    if isinstance(payload, ValidationReport):
        return payload
    return ValidationReport.model_validate(payload)


def _format_validation_report(report: ValidationReport) -> str:
    lines = [
        f"Validation summary: {report.summary}",
        f"Readiness verdict: {report.readiness_verdict}",
        f"Present fields: {', '.join(report.present_fields) if report.present_fields else 'none'}",
        f"Missing required fields: {', '.join(report.missing_required_fields) if report.missing_required_fields else 'none'}",
        "Field evidence:",
    ]
    for item in report.field_results:
        if item.present and item.evidence_snippets:
            evidence = "; ".join(item.evidence_snippets)
            lines.append(f"- {item.name}: present via {evidence}")
        elif item.present:
            lines.append(f"- {item.name}: present")
        else:
            lines.append(f"- {item.name}: missing")
    return "\n".join(lines)


def _format_brief_for_llm(state: GraphState) -> str:
    lines = [
        "Original brief:",
        state["brief"],
    ]
    if state.get("validation_report"):
        lines.extend(
            [
                "",
                "Deterministic validation report:",
                _format_validation_report(_load_validation_report(state["validation_report"])),
                "",
                "Treat the validation report as authoritative.",
            ]
        )

    lines.extend(
        [
            "",
            "Return both:",
            "- a structured planning brief",
            "- a workflow analysis",
        ]
    )
    return "\n".join(lines)


def _format_plan_input(
    structured_brief: StructuredBrief,
    workflow_analysis: WorkflowAnalysis,
    reference_patterns: list[str],
    validation_report: ValidationReport | None = None,
) -> str:
    patterns_block = "\n".join(f"- {pattern}" for pattern in reference_patterns)
    lines = [f"""Structured brief:
{structured_brief.model_dump_json(indent=2)}

Workflow analysis:
{workflow_analysis.model_dump_json(indent=2)}

Reference patterns:
{patterns_block}

Produce a scoped first-pass deployment plan.
"""]
    if validation_report:
        lines.insert(
            1,
            f"""Deterministic validation report:
{validation_report.model_dump_json(indent=2)}

""",
        )
    return "".join(lines)


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


def _summarize_validation_result(report: ValidationReport) -> list[str]:
    return [
        f"{item.name}: {'present' if item.present else 'missing'}"
        for item in report.field_results
    ]


def _apply_validation_guards(
    draft: DraftPlan,
    validation_report: ValidationReport | None,
) -> DraftPlan:
    if not validation_report:
        return draft

    guardrails = list(draft.guardrails)
    rollout = list(draft.rollout_checklist)
    limitations = list(draft.limitations)
    tool_plan = list(draft.tool_plan)

    validator_tool = "Required-field validator with evidence snippets"
    if validator_tool not in tool_plan:
        tool_plan.insert(0, validator_tool)

    update = {"tool_plan": tool_plan}
    if validation_report.missing_required_fields:
        missing = ", ".join(validation_report.missing_required_fields)
        clarification_step = f"Clarify required fields before rollout: {missing}."
        if clarification_step not in rollout:
            rollout.insert(0, clarification_step)

        validation_guardrail = "Do not treat validator-marked missing fields as implicitly resolved."
        if validation_guardrail not in guardrails:
            guardrails.append(validation_guardrail)

        validation_limitation = f"The intake validator marked this request incomplete: missing {missing}."
        if validation_limitation not in limitations:
            limitations.append(validation_limitation)

        update.update(
            {
                "confidence": min(draft.confidence, 0.58),
                "guardrails": guardrails,
                "rollout_checklist": rollout,
                "limitations": limitations,
                "approval_prompt": (
                    "Approve this plan only if it stays clarification-first and keeps human review in place."
                ),
            }
        )
    return draft.model_copy(update=update)


def load_and_validate_request(state: GraphState) -> GraphState:
    if state.get("request_packet") or state.get("request_file"):
        packet = (
            _load_request_packet(state["request_packet"])
            if state.get("request_packet")
            else load_request_packet(state["request_file"])
        )
        schema = (
            _load_validation_schema(state["validation_schema"])
            if state.get("validation_schema")
            else load_validation_schema(state.get("schema_file"))
        )
        if packet.workflow_type != schema.workflow_type:
            raise ValueError(
                f"Request workflow_type '{packet.workflow_type}' does not match schema workflow_type '{schema.workflow_type}'."
            )
        report = validate_request_packet(packet, schema)
        brief = build_brief_from_request(packet, report)
        return {
            "brief": brief,
            "source_mode": "request_file",
            "request_packet": packet.model_dump(by_alias=True),
            "validation_schema": schema.model_dump(),
            "validation_report": report.model_dump(),
        }

    return {"source_mode": "brief"}


def render_final_output(state: GraphState) -> str:
    structured_brief = _load_structured_brief(state["structured_brief"])
    workflow_analysis = _load_workflow_analysis(state["workflow_analysis"])
    draft_plan = _load_draft_plan(state["draft_plan"])
    reviewer_notes = state.get("reviewer_notes", "").strip()
    validation_report = (
        _load_validation_report(state["validation_report"])
        if state.get("validation_report")
        else None
    )
    request_packet = (
        _load_request_packet(state["request_packet"])
        if state.get("request_packet")
        else None
    )

    lines = [
        f"# {draft_plan.title}",
        "",
        "## Workflow Summary",
        structured_brief.problem_statement,
        "",
        "## Recommended Agent Goal",
        draft_plan.agent_goal,
        "",
        "## Proposed Pilot Workflow Stages",
    ]
    lines.extend(f"- {node}" for node in draft_plan.graph_nodes)
    if validation_report and request_packet:
        lines.extend(
            [
                "",
                "## Intake Validation",
                f"- request_id: {request_packet.request_id}",
                f"- readiness_verdict: {validation_report.readiness_verdict}",
                f"- present_fields: {', '.join(validation_report.present_fields) if validation_report.present_fields else 'none'}",
                f"- missing_required_fields: {', '.join(validation_report.missing_required_fields) if validation_report.missing_required_fields else 'none'}",
                "",
                "## Validator Evidence",
            ]
        )
        lines.extend(f"- {item}" for item in _summarize_validation_result(validation_report))
        for item in validation_report.field_results:
            if item.evidence_snippets:
                lines.extend(
                    f"- {item.name} evidence: {snippet}" for snippet in item.evidence_snippets
                )
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
    validation_report = (
        _load_validation_report(state["validation_report"])
        if state.get("validation_report")
        else None
    )

    lines = [
        "# Additional Context Needed",
        "",
        "The workflow can be planned, but the current brief is not strong enough to recommend rollout without more detail.",
        "",
    ]
    if validation_report:
        lines.extend(
            [
                "## Intake Validation",
                f"- readiness_verdict: {validation_report.readiness_verdict}",
                f"- missing_required_fields: {', '.join(validation_report.missing_required_fields) if validation_report.missing_required_fields else 'none'}",
                "",
            ]
        )
    lines.extend(
        [
        "## Missing Information",
        ]
    )
    lines.extend(f"- {item}" for item in structured_brief.missing_information)
    if validation_report and validation_report.missing_required_fields:
        lines.extend(
            f"- validator missing field: {field}" for field in validation_report.missing_required_fields
        )
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


def ingest_and_analyze_workflow(state: GraphState) -> GraphState:
    validation_report = (
        _load_validation_report(state["validation_report"])
        if state.get("validation_report")
        else None
    )
    if get_settings().demo_mode:
        structured_brief = demo_structured_brief(state["brief"])
        workflow_analysis = demo_workflow_analysis(
            structured_brief,
            state["brief"],
            validation_report=validation_report,
        )
        reference_patterns = get_reference_patterns(workflow_analysis.workflow_type)
        return {
            "structured_brief": structured_brief.model_dump(),
            "workflow_analysis": workflow_analysis.model_dump(),
            "reference_patterns": reference_patterns,
        }

    intake_analysis = _structured_invoke(
        IntakeAnalysis,
        INGEST_AND_ANALYZE_SYSTEM_PROMPT,
        _format_brief_for_llm(state),
    )
    structured_brief = intake_analysis.structured_brief
    workflow_analysis = intake_analysis.workflow_analysis
    reference_patterns = get_reference_patterns(workflow_analysis.workflow_type)
    return {
        "structured_brief": structured_brief.model_dump(),
        "workflow_analysis": workflow_analysis.model_dump(),
        "reference_patterns": reference_patterns,
    }


def draft_plan(state: GraphState) -> GraphState:
    structured_brief = _load_structured_brief(state["structured_brief"])
    workflow_analysis = _load_workflow_analysis(state["workflow_analysis"])
    reference_patterns = state["reference_patterns"]
    validation_report = (
        _load_validation_report(state["validation_report"])
        if state.get("validation_report")
        else None
    )
    if get_settings().demo_mode:
        draft = demo_draft_plan(
            structured_brief,
            workflow_analysis,
            reference_patterns,
            validation_report=validation_report,
        )
        return {
            "draft_plan": _apply_validation_guards(draft, validation_report).model_dump()
        }

    draft = _structured_invoke(
        DraftPlan,
        DRAFT_PLAN_SYSTEM_PROMPT,
        _format_plan_input(
            structured_brief,
            workflow_analysis,
            reference_patterns,
            validation_report=validation_report,
        ),
    )
    return {
        "draft_plan": _apply_validation_guards(draft, validation_report).model_dump()
    }


def review_gate(state: GraphState) -> GraphState:
    draft = _load_draft_plan(state["draft_plan"])
    workflow_analysis = _load_workflow_analysis(state["workflow_analysis"])
    validation_report = (
        _load_validation_report(state["validation_report"])
        if state.get("validation_report")
        else None
    )
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
            "readiness_verdict": validation_report.readiness_verdict if validation_report else None,
            "missing_required_fields": validation_report.missing_required_fields if validation_report else [],
            "instructions": "Reply with {'approved': true, 'notes': '...'} to finalize with a human override if needed, or send revision notes to escalate for more context.",
        }
    )
    decision, notes = parse_reviewer_response(response)
    return {
        "reviewer_decision": decision,
        "reviewer_notes": notes,
    }


def route_after_review(state: GraphState) -> Literal["finalize_plan", "escalate_request"]:
    if state.get("reviewer_decision") == "approve":
        return "finalize_plan"
    return "escalate_request"


def finalize_plan(state: GraphState) -> GraphState:
    return {"final_output": render_final_output(state)}


def escalate_request(state: GraphState) -> GraphState:
    return {"final_output": render_escalation_output(state)}
