# Architecture Notes

## Goal

This graph is intentionally small. The project is trying to show the core mechanics of a deployment-minded agent workflow, not maximum complexity.

## Nodes

### `load_and_validate_request`

Loads a local JSON request packet, validates it against a required-fields schema, and produces a deterministic readiness report with evidence snippets.

This is the thin real-world integration boundary in the repo. It is intentionally local and narrow:

- file-backed input instead of a mocked prompt blob
- required-field validation before planning
- evidence snippets to show where detected fields came from

### `ingest_and_analyze_workflow`

Combines two concerns into one model step:

- turns a messy request into a structured planning brief
- assesses the workflow like an operator planning a rollout

- what kind of workflow this is
- where humans should stay involved
- what can go wrong
- how confident the system should be

### `draft_plan`

Creates a scoped first-pass deployment plan with nodes, tool suggestions, guardrails, and a rollout checklist.

### `review_gate`

Uses a LangGraph interrupt to pause and wait for human approval or revision notes.

### `finalize_plan`

Builds the final markdown output when the plan is approved.

### `escalate_request`

Returns a conservative escalation output when the reviewer asks for revision or more context.

## Why This Shape

This architecture maps to how LangChain publicly frames LangGraph:

- durable, stateful workflows
- human-in-the-loop approval
- explicit control over routing
- systems that acknowledge uncertainty

The combined intake-analysis step is intentional. The earlier version separated those into two model calls, but that added unnecessary latency without improving control flow.

## What Is Missing On Purpose

- networked or cloud-hosted integrations
- external retrieval
- authentication
- persistent storage
- a custom UI

Those can come later. For the application artifact, the most important thing is that the graph is coherent, easy to explain, and shows one thin deterministic integration boundary before the model does planning work.
