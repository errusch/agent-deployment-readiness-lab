from __future__ import annotations

import json
import re
from pathlib import Path

from .schemas import (
    FieldValidationResult,
    RequestPacket,
    ValidationReport,
    ValidationSchema,
)


ONBOARDING_SCHEMA_DATA = {
    "workflow_type": "onboarding_ops",
    "required_fields": [
        {
            "name": "customer_name",
            "description": "Customer or company name",
            "required": True,
        },
        {
            "name": "implementation_goal",
            "description": "What the customer needs implemented",
            "required": True,
        },
        {
            "name": "timeline",
            "description": "Requested or expected timeline",
            "required": True,
        },
        {
            "name": "primary_contact",
            "description": "Who to follow up with",
            "required": True,
        },
    ],
}


FIELD_LABELS: dict[str, list[str]] = {
    "customer_name": ["customer name", "company", "customer"],
    "implementation_goal": ["implementation goal", "goal", "need", "needs"],
    "timeline": ["timeline", "deadline", "target date", "go-live", "launch"],
    "primary_contact": ["primary contact", "contact", "point of contact"],
}


def load_request_packet(path: str) -> RequestPacket:
    payload = json.loads(Path(path).read_text())
    return RequestPacket.model_validate(payload)


def load_validation_schema(path: str | None = None) -> ValidationSchema:
    if path:
        payload = json.loads(Path(path).read_text())
        return ValidationSchema.model_validate(payload)
    return ValidationSchema.model_validate(ONBOARDING_SCHEMA_DATA)


def _normalize_value(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _find_metadata_evidence(packet: RequestPacket, field_name: str) -> tuple[str | None, list[str]]:
    value = _normalize_value(packet.metadata.get(field_name))
    if not value:
        return None, []
    return value, [f"metadata.{field_name}: {value}"]


def _thread_evidence(packet: RequestPacket, label: str) -> tuple[str | None, list[str]]:
    pattern = re.compile(rf"(?im)^\s*{re.escape(label)}\s*:\s*(.+?)\s*$")
    for index, message in enumerate(packet.thread, start=1):
        match = pattern.search(message.body)
        if match:
            value = _normalize_value(match.group(1))
            if value:
                snippet = match.group(0).strip()
                return value, [f"thread[{index}] {message.sender}: {snippet}"]
    return None, []


def _find_thread_evidence(packet: RequestPacket, field_name: str) -> tuple[str | None, list[str]]:
    for label in FIELD_LABELS.get(field_name, [field_name.replace("_", " ")]):
        value, evidence = _thread_evidence(packet, label)
        if value:
            return value, evidence
    return None, []


def validate_request_packet(
    packet: RequestPacket,
    schema: ValidationSchema,
) -> ValidationReport:
    packet = RequestPacket.model_validate(packet.model_dump(by_alias=True))
    field_results: list[FieldValidationResult] = []
    present_fields: list[str] = []
    missing_required_fields: list[str] = []

    for field_def in schema.required_fields:
        value, evidence = _find_metadata_evidence(packet, field_def.name)
        if value is None:
            value, evidence = _find_thread_evidence(packet, field_def.name)

        present = value is not None
        if present:
            present_fields.append(field_def.name)
        elif field_def.required:
            missing_required_fields.append(field_def.name)

        field_results.append(
            FieldValidationResult(
                name=field_def.name,
                description=field_def.description,
                required=field_def.required,
                present=present,
                value=value,
                evidence_snippets=evidence,
            )
        )

    verdict = "ready_for_draft" if not missing_required_fields else "needs_context"
    summary = (
        "All required onboarding fields were found in the request packet."
        if verdict == "ready_for_draft"
        else "The request packet is missing required onboarding fields and should be treated as clarification-first."
    )
    return ValidationReport(
        workflow_type=schema.workflow_type,
        readiness_verdict=verdict,
        present_fields=present_fields,
        missing_required_fields=missing_required_fields,
        field_results=field_results,
        summary=summary,
    )


def build_brief_from_request(
    packet: RequestPacket,
    report: ValidationReport,
) -> str:
    customer_name = _normalize_value(packet.metadata.get("customer_name")) or packet.subject
    lines = [
        f"Help the ops team process onboarding intake for {customer_name} using a reviewable triage and handoff workflow.",
        "",
        f"Request ID: {packet.request_id}",
        f"Workflow type: {packet.workflow_type}",
        f"Subject: {packet.subject}",
        "",
        "Metadata:",
    ]
    if packet.metadata:
        for key, value in packet.metadata.items():
            lines.append(f"- {key}: {value}")
    else:
        lines.append("- None provided")

    lines.extend(["", "Thread excerpts:"])
    if packet.thread:
        for message in packet.thread:
            body = " ".join(message.body.split())
            lines.append(
                f"- {message.sender} @ {message.timestamp}: {body[:220]}"
            )
    else:
        lines.append("- No thread messages were provided.")

    lines.extend(
        [
            "",
            "Validation summary:",
            f"- readiness_verdict: {report.readiness_verdict}",
            f"- present_fields: {', '.join(report.present_fields) if report.present_fields else 'none'}",
            f"- missing_required_fields: {', '.join(report.missing_required_fields) if report.missing_required_fields else 'none'}",
            "- validator outputs are authoritative; do not invent missing fields.",
        ]
    )
    return "\n".join(lines)
