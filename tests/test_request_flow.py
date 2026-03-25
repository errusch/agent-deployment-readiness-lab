from pathlib import Path

from langgraph.types import Command

from agent_deployment_readiness_lab.config import get_settings
from agent_deployment_readiness_lab.graph import build_graph


def test_request_file_flow_interrupt_then_finalize(monkeypatch):
    monkeypatch.setenv("AGENT_DEPLOYMENT_DEMO_MODE", "true")
    get_settings.cache_clear()
    graph = build_graph()
    request_file = Path("examples/inbox/onboarding/missing_fields_request.json")
    schema_file = Path("examples/schemas/onboarding_required_fields.json")
    config = {"configurable": {"thread_id": "test-request-flow"}}

    result = graph.invoke(
        {
            "brief": "",
            "request_file": str(request_file),
            "schema_file": str(schema_file),
        },
        config=config,
    )
    interrupt = result["__interrupt__"][0].value
    assert interrupt["readiness_verdict"] == "needs_context"
    assert "timeline" in interrupt["missing_required_fields"]

    resumed = graph.invoke(
        Command(resume={"approved": True, "notes": "Proceed as a clarification-first pilot."}),
        config=config,
    )
    assert "## Intake Validation" in resumed["final_output"]
    assert "timeline" in resumed["final_output"]
    assert "## Proposed Pilot Workflow Stages" in resumed["final_output"]


def test_request_file_flow_auto_escalates_on_revision(monkeypatch):
    monkeypatch.setenv("AGENT_DEPLOYMENT_DEMO_MODE", "true")
    get_settings.cache_clear()
    graph = build_graph()
    request_file = Path("examples/inbox/onboarding/missing_fields_request.json")
    schema_file = Path("examples/schemas/onboarding_required_fields.json")
    config = {"configurable": {"thread_id": "test-request-escalation"}}

    graph.invoke(
        {
            "brief": "",
            "request_file": str(request_file),
            "schema_file": str(schema_file),
        },
        config=config,
    )
    resumed = graph.invoke(
        Command(resume={"approved": False, "notes": "Need more customer detail."}),
        config=config,
    )
    assert resumed["final_output"].startswith("# Additional Context Needed")
