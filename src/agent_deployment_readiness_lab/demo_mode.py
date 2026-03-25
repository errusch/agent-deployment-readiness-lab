from __future__ import annotations

from .schemas import DraftPlan, StructuredBrief, WorkflowAnalysis


def infer_workflow_type(text: str) -> str:
    lowered = text.lower()
    if "onboarding" in lowered:
        return "onboarding_ops"
    if "executive" in lowered or "briefing" in lowered:
        return "executive_support"
    if "support" in lowered or "ticket" in lowered or "handoff" in lowered:
        return "support_handoff"
    if "research" in lowered or "diligence" in lowered:
        return "research_workflow"
    return "general_ops"


def split_lines(text: str) -> list[str]:
    return [line.strip("- ").strip() for line in text.splitlines() if line.strip()]


def demo_structured_brief(brief: str) -> StructuredBrief:
    lines = split_lines(brief)
    problem_statement = lines[0] if lines else "Turn a messy workflow request into a reviewable deployment plan."
    target_users: list[str] = []
    desired_outcomes: list[str] = []
    constraints: list[str] = []
    current_process: list[str] = []

    lowered = brief.lower()
    if "ops" in lowered:
        target_users.append("Operations team")
    if "executive" in lowered:
        target_users.append("Executive support team")
    if "support" in lowered:
        target_users.append("Support team")
        target_users.append("Engineering team")
    if not target_users:
        target_users.append("Business operations team")

    for line in lines[1:]:
        lower = line.lower()
        if "want" in lower or "should" in lower or "need" in lower:
            desired_outcomes.append(line)
        elif "constraint" in lower or "human" in lower or "approval" in lower:
            constraints.append(line)
        else:
            current_process.append(line)

    if not desired_outcomes:
        desired_outcomes = [
            "Create a cleaner workflow summary.",
            "Flag missing information early.",
            "Produce a reviewable handoff or action plan.",
        ]

    if not constraints:
        constraints = [
            "Keep a human approval point before high-stakes output.",
            "Do not guess when requirements are unclear.",
        ]

    return StructuredBrief(
        problem_statement=problem_statement,
        target_users=target_users,
        current_process=current_process[:5],
        desired_outcomes=desired_outcomes[:5],
        constraints=constraints[:5],
        assumptions=[
            "This is a pilot-friendly first version.",
            "The team wants a practical workflow, not a broad autonomous system.",
        ],
        missing_information=[
            "No exact source systems or tools were specified.",
            "Success metrics for the pilot were not explicitly defined.",
        ],
    )


def demo_workflow_analysis(structured_brief: StructuredBrief, original_brief: str) -> WorkflowAnalysis:
    workflow_type = infer_workflow_type(original_brief)
    confidence = 0.78 if workflow_type != "general_ops" else 0.62

    review_points = [
        "Approve any external-facing or high-stakes output before it is used.",
        "Review missing-information flags before treating the handoff as complete.",
    ]
    failure_modes = [
        "The workflow could overstate confidence when the brief is incomplete.",
        "The system could produce a clean handoff that hides important uncertainty.",
        "Users may skip the review gate if the process feels too polished.",
    ]
    business_risks = [
        "Low-quality handoffs can create downstream rework.",
        "Ambiguous ownership can make the workflow look successful while hiding delays.",
    ]

    if workflow_type == "executive_support":
        review_points.append("Verify that inferred action items are not presented as executive intent.")
        failure_modes.append("Condensing context too aggressively may remove nuance the executive cares about.")
    if workflow_type == "support_handoff":
        review_points.append("Review any priority or severity labels before sending to engineering.")
        failure_modes.append("Weak evidence may be mistaken for reproducible signal.")
    if workflow_type == "onboarding_ops":
        review_points.append("Check customer-facing follow-up questions before sending them.")
        failure_modes.append("Missing onboarding requirements may be framed as complete intake.")

    return WorkflowAnalysis(
        workflow_type=workflow_type,
        reasoning_summary=(
            "This workflow fits a deployment-readiness pattern: normalize intake, make uncertainty visible, "
            "draft a structured plan, and force review before finalizing."
        ),
        automation_opportunities=[
            "Normalize inconsistent intake into a standard planning structure.",
            "Flag missing information before downstream teams begin work.",
            "Draft a reusable handoff packet and rollout checklist.",
        ],
        required_capabilities=[
            "Structured summarization",
            "Checklist generation",
            "Escalation when confidence is weak",
            "Human review before final output",
        ],
        human_review_points=review_points,
        likely_failure_modes=failure_modes,
        business_risks=business_risks,
        recommended_tools=[
            "Brief intake form or inbox adapter",
            "Checklist template",
            "Approval inbox or LangGraph interrupt review step",
        ],
        confidence=confidence,
    )


def demo_draft_plan(
    structured_brief: StructuredBrief,
    workflow_analysis: WorkflowAnalysis,
    reference_patterns: list[str],
) -> DraftPlan:
    title_map = {
        "onboarding_ops": "Onboarding Workflow Deployment Plan",
        "executive_support": "Executive Briefing Workflow Deployment Plan",
        "support_handoff": "Support Handoff Deployment Plan",
        "research_workflow": "Research Workflow Deployment Plan",
        "general_ops": "Operations Workflow Deployment Plan",
    }
    title = title_map.get(workflow_analysis.workflow_type, "Agent Workflow Deployment Plan")
    graph_nodes = [
        "Ingest brief",
        "Analyze workflow",
        "Draft deployment plan",
        "Review gate",
        "Finalize or escalate",
    ]
    rollout = [
        "Run the workflow on 5 to 10 representative examples.",
        "Track where the system asks for missing context instead of improvising.",
        "Review failure modes weekly before expanding scope.",
        "Keep the first rollout narrow and approval-heavy.",
    ]
    guardrails = [
        "Do not claim requirements are complete when source input is weak.",
        "Do not skip human review for external-facing or high-risk outputs.",
        "Surface uncertainty directly instead of smoothing it away.",
    ]

    return DraftPlan(
        title=title,
        executive_summary=(
            "Turn a vague workflow request into a conservative deployment plan with explicit review, "
            "risk handling, and rollout steps."
        ),
        agent_goal=(
            "Help the team move from a rough workflow idea to a pilot-ready plan that a human can inspect, "
            "approve, and improve."
        ),
        graph_nodes=graph_nodes,
        tool_plan=workflow_analysis.recommended_tools,
        guardrails=guardrails,
        rollout_checklist=rollout,
        limitations=[
            "This demo does not include live integrations or persistent storage.",
            "The first rollout should focus on review quality rather than full autonomy.",
            "Confidence should be interpreted as planning confidence, not business approval.",
        ],
        approval_prompt=(
            "Approve this deployment plan if it is conservative enough for a pilot. "
            "If not, ask for revision or more context."
        ),
        confidence=workflow_analysis.confidence,
    )
