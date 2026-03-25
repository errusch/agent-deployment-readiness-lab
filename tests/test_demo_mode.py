from agent_deployment_readiness_lab.demo_mode import (
    demo_draft_plan,
    demo_structured_brief,
    demo_workflow_analysis,
)
from agent_deployment_readiness_lab.nodes import get_reference_patterns


def test_demo_mode_onboarding_path_produces_expected_shape():
    brief = (
        "We need an AI workflow to help our ops team handle client onboarding emails, "
        "summarize requirements, flag missing info, and create a handoff plan."
    )
    structured = demo_structured_brief(brief)
    analysis = demo_workflow_analysis(structured, brief)
    draft = demo_draft_plan(
        structured,
        analysis,
        get_reference_patterns(analysis.workflow_type),
    )

    assert analysis.workflow_type == "onboarding_ops"
    assert draft.title == "Onboarding Workflow Deployment Plan"
    assert "Review gate" in draft.graph_nodes
    assert draft.confidence >= 0.7

