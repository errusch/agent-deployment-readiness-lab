from agent_deployment_readiness_lab.nodes import (
    get_reference_patterns,
    parse_reviewer_response,
    render_escalation_output,
    render_final_output,
)
from agent_deployment_readiness_lab.schemas import DraftPlan, StructuredBrief, WorkflowAnalysis


def build_sample_state():
    return {
        "brief": "Sample brief",
        "structured_brief": StructuredBrief(
            problem_statement="Create a better onboarding handoff workflow.",
            target_users=["Ops team"],
            current_process=["Email intake", "Manual follow-up"],
            desired_outcomes=["Cleaner handoffs"],
            constraints=["Human approval required"],
            assumptions=["Pilot workflow"],
            missing_information=["No SLA was provided"],
        ),
        "workflow_analysis": WorkflowAnalysis(
            workflow_type="onboarding_ops",
            reasoning_summary="This is an intake-to-handoff workflow with approval requirements.",
            automation_opportunities=["Summarize requests", "Flag missing details"],
            required_capabilities=["Email summarization", "Checklist drafting"],
            human_review_points=["Customer-facing messaging", "High-risk edge cases"],
            likely_failure_modes=["Inventing missing requirements"],
            business_risks=["Bad handoffs could slow onboarding"],
            recommended_tools=["Email ingest", "Checklist template"],
            confidence=0.72,
        ),
        "draft_plan": DraftPlan(
            title="Onboarding Ops Deployment Plan",
            executive_summary="Normalize intake, draft a handoff, and require approval before finalizing.",
            agent_goal="Help ops turn messy intake into a reviewable handoff packet.",
            graph_nodes=["Ingest brief", "Analyze workflow", "Draft plan", "Review gate"],
            tool_plan=["Email parser", "Checklist template"],
            guardrails=["Do not guess missing requirements"],
            rollout_checklist=["Run with 5 pilot requests", "Review failure cases weekly"],
            limitations=["No live integrations yet"],
            approval_prompt="Approve this plan before using it in a pilot.",
            confidence=0.72,
        ),
        "reviewer_notes": "Keep the first pilot narrow.",
    }


def test_parse_reviewer_response_with_bool():
    assert parse_reviewer_response(True) == ("approve", "")
    assert parse_reviewer_response(False) == ("revise", "")


def test_parse_reviewer_response_with_dict():
    assert parse_reviewer_response({"approved": True, "notes": "Ship it"}) == (
        "approve",
        "Ship it",
    )
    assert parse_reviewer_response({"approved": False, "notes": "Need more detail"}) == (
        "revise",
        "Need more detail",
    )


def test_reference_patterns_fall_back_to_general_ops():
    patterns = get_reference_patterns("not_real")
    assert len(patterns) == 3


def test_render_final_output_contains_expected_sections():
    output = render_final_output(build_sample_state())
    assert "## Workflow Summary" in output
    assert "## Rollout Checklist" in output
    assert "## Reviewer Notes" in output


def test_render_escalation_output_contains_missing_information():
    output = render_escalation_output(build_sample_state())
    assert "## Missing Information" in output
    assert "No SLA was provided" in output
