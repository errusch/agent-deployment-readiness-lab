from agent_deployment_readiness_lab.intake_adapter import (
    build_brief_from_request,
    load_validation_schema,
    validate_request_packet,
)
from agent_deployment_readiness_lab.schemas import RequestPacket, RequestThreadMessage


def build_complete_packet() -> RequestPacket:
    return RequestPacket.model_validate(
        {
            "request_id": "onb-001",
            "workflow_type": "onboarding_ops",
            "subject": "New client onboarding request",
            "thread": [
                {
                    "from": "client",
                    "timestamp": "2026-03-25T09:00:00Z",
                    "body": "\n".join(
                        [
                            "Customer name: Acme Manufacturing",
                            "Implementation goal: Set up onboarding triage and a handoff packet.",
                            "Timeline: Pilot live by April 15.",
                            "Primary contact: Sarah Kim (sarah@acme.com)",
                        ]
                    ),
                }
            ],
            "metadata": {
                "customer_name": "Acme Manufacturing",
                "account_owner": "Jane Doe",
                "priority": "normal",
            },
        }
    )


def test_validator_detects_complete_request():
    packet = build_complete_packet()
    schema = load_validation_schema()
    report = validate_request_packet(packet, schema)
    assert report.readiness_verdict == "ready_for_draft"
    assert report.missing_required_fields == []
    assert "implementation_goal" in report.present_fields


def test_validator_detects_missing_fields_with_evidence():
    packet = build_complete_packet().model_copy(
        update={
            "thread": [
                RequestThreadMessage(
                    **{
                        "from": "client",
                        "timestamp": "2026-03-25T09:00:00Z",
                        "body": "Customer name: Acme Manufacturing\nImplementation goal: Set up onboarding triage.",
                    }
                )
            ]
        }
    )
    schema = load_validation_schema()
    report = validate_request_packet(packet, schema)
    assert report.readiness_verdict == "needs_context"
    assert set(report.missing_required_fields) == {"timeline", "primary_contact"}
    customer_field = next(item for item in report.field_results if item.name == "customer_name")
    assert customer_field.evidence_snippets


def test_build_brief_from_request_mentions_missing_fields():
    packet = build_complete_packet()
    schema = load_validation_schema()
    report = validate_request_packet(packet, schema)
    brief = build_brief_from_request(packet, report)
    assert "Validation summary:" in brief
    assert "missing_required_fields: none" in brief
