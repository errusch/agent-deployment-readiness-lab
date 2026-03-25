# Pilot Plan: Email-Based Onboarding Triage and Handoff Assistant

## Workflow Summary
Help the ops team process client onboarding emails by summarizing incoming requests, identifying missing information, recommending the next step, and preparing a handoff packet for implementation with human approval for any customer-facing response.

## Recommended Agent Goal
Turn incoming onboarding emails into a reviewable internal summary, a gap checklist, a suggested next action, and a standardized handoff packet for implementation, while requiring human approval before any customer-facing response is sent.

## Proposed Graph Nodes
- 1) Intake email and preserve thread context
- 2) Extract request details and summarize intent
- 3) Compare against required onboarding fields and flag missing information
- 4) Recommend next internal action: handoff, clarify, or escalate
- 5) Generate implementation handoff packet
- 6) Route outputs to human review and approval
- 7) Send approved customer-facing draft or archive for handoff

## Tool Plan
- Email ingestion with thread/context capture
- LLM-based extraction and summarization for internal drafting
- Checklist validator against a defined onboarding schema
- Template-based handoff packet generator
- Human approval step for customer-facing replies and ambiguous cases
- Basic audit log of inputs, outputs, and approvals

## Human Review Points
- Approve any customer-facing email before sending.
- Review missing-information flags to ensure they are accurate.
- Confirm the recommended next action when the request is ambiguous.
- Validate the handoff packet before it goes to implementation.
- Handle edge cases or priority exceptions manually.

## Likely Failure Modes
- The model hallucinates missing details or implied requirements.
- The summary misses a critical constraint buried in the email thread.
- A partial request is treated as complete and handed off too early.
- Customer-facing drafts are sent without proper review.
- The handoff packet is inconsistent across cases and hard for implementation to use.
- Email thread context is lost when multiple replies exist.

## Guardrails
- Do not invent missing requirements or implied commitments.
- Treat uncertain or partial requests as incomplete until a human confirms otherwise.
- Do not send any customer-facing message without explicit approval.
- Keep the first pilot to a narrow request type or a small set of onboarding email patterns.
- Require evidence links or quoted text for any flagged missing field or recommendation.
- Escalate ambiguous, high-priority, or exception cases to a human reviewer immediately.

## Rollout Checklist
- Define a minimal required-field checklist for a complete onboarding request.
- Select a small pilot inbox or subset of onboarding emails.
- Create a standard summary format and implementation handoff template.
- Set approval rules for outbound customer-facing drafts and ambiguous cases.
- Run the workflow in shadow/review mode on a small sample before allowing operational use.
- Measure summary accuracy, missing-field detection, handoff completeness, and time saved.
- Review pilot failures weekly and tighten the checklist before expanding scope.

## Confidence
0.92

## Reviewer Notes
Looks good. Keep the rollout conservative.

## Limitations
- This pilot will not fully automate onboarding or resolve ambiguous requests end-to-end.
- Quality depends on having a clear required-field schema and consistent email thread access.
- The system may still miss subtle requirements buried in long threads or attachments.
- It is not designed to create enterprise-wide ticketing, CRM, or document workflows in the first pass.
- Customer communication remains manually approved, so the workflow will not eliminate human review time.