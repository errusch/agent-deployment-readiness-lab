# Pilot Plan: AI-Assisted Executive Briefing Triage

## Workflow Summary
Create an AI-assisted executive support workflow that turns messy incoming notes, Slack messages, and email threads into a concise briefing with action items, decision points, and missing context, while clearly separating confirmed facts from inferred points and flagging what requires human review before anything is shared onward.

## Recommended Agent Goal
Turn fragmented incoming executive material into a concise, reviewable briefing that separates confirmed facts from inference, surfaces missing context, and flags items requiring human approval before any onward sharing.

## Proposed Graph Nodes
- 1. Intake and normalize source material
- 2. Extract facts, actions, decisions, owners, dates, and open questions
- 3. Draft a short briefing in a fixed template with fact/inference separation
- 4. Flag ambiguity, missing context, and high-risk content for human review
- 5. Human reviewer approves, edits, or rejects the draft
- 6. Final briefing may be shared by a human only; system records audit trail

## Tool Plan
- Slack and email ingestion for selected inboxes/channels only
- Basic text normalization and thread grouping
- LLM-based extraction and summarization with a strict template
- Uncertainty and ambiguity detector for names, dates, owners, and commitments
- Source reference capture for each key bullet where available
- Human review queue for approve/edit/reject
- Audit log of inputs, draft versions, and reviewer actions
- Optional redaction step for sensitive personal or regulated content

## Human Review Points
- Before any briefing is sent onward
- When the model infers meaning not explicitly stated
- When names, dates, owners, or commitments are ambiguous
- When the source material conflicts across Slack and email
- When the content includes sensitive, legal, HR, or financial implications
- When the briefing changes the tone or urgency of the original message

## Likely Failure Modes
- Hallucinated action items or decisions not supported by source material
- Blending inferred context with confirmed facts
- Missing important nuances in terse executive language
- Over-summarizing and dropping critical detail
- Failing to capture implicit deadlines or ownership
- Using the wrong tone or priority level
- Forwarding sensitive information without proper review
- Poor handling of conflicting messages across channels

## Guardrails
- No autonomous sending or posting to external recipients
- Always label output sections as confirmed facts, inferred points, and open questions
- If source material conflicts, mark conflict explicitly rather than resolving it silently
- Do not invent owners, dates, decisions, or commitments
- Require human review when content is sensitive, ambiguous, or likely to change meaning or tone
- Keep the briefing short; prefer omissions flagged as open questions over verbose speculation
- Preserve traceability to original messages when possible
- Limit pilot scope to a small set of trusted users and source channels

## Rollout Checklist
- Define the standard briefing template with 3-5 fixed sections
- Choose the primary human reviewer role for the pilot
- Select a small intake scope: a few executives and a limited set of channels/inboxes
- Confirm permissioned access to source content and retention rules
- Agree on what counts as confirmed fact versus inferred context
- Set a latency target for first draft turnaround
- Test on a small sample of historical threads before live use
- Review outputs for accuracy, brevity, and missing context flags
- Establish a manual approval step before any outward sharing
- Measure time saved, correction rate, and reviewer trust

## Confidence
0.94

## Reviewer Notes
Looks good. Keep the rollout conservative.

## Limitations
- The workflow will not reliably resolve vague executive language without human input
- It may miss implicit context that a human would infer from organizational history
- Source traceability may be incomplete if messages are forwarded or paraphrased heavily
- The pilot will not handle every compliance or records-management requirement by default
- It is not designed to replace executive judgment or assistant review
- Quality will depend on the consistency of source formatting and available permissions
