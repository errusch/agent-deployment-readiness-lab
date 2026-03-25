# Architecture Notes

## Goal

This graph is intentionally small. The project is trying to show the core mechanics of a deployment-minded agent workflow, not maximum complexity.

## Nodes

### `ingest_brief`

Turns a messy request into a structured planning brief.

### `analyze_workflow`

Assesses the workflow like an operator planning a rollout:

- what kind of workflow this is
- where humans should stay involved
- what can go wrong
- how confident the system should be

### `draft_plan`

Creates a scoped first-pass deployment plan with nodes, tool suggestions, guardrails, and a rollout checklist.

### `review_gate`

Uses a LangGraph interrupt to pause and wait for human approval or revision notes.

### `finalize_plan`

Builds the final markdown output when the plan is approved and confidence is adequate.

### `escalate_request`

Returns a conservative escalation output when confidence is weak or the reviewer asks for revision.

## Why This Shape

This architecture maps to how LangChain publicly frames LangGraph:

- durable, stateful workflows
- human-in-the-loop approval
- explicit control over routing
- systems that acknowledge uncertainty

## What Is Missing On Purpose

- live integrations
- external retrieval
- authentication
- persistent storage
- a custom UI

Those can come later. For the application artifact, the most important thing is that the graph is coherent and easy to explain.

