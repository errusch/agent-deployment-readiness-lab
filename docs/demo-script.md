# Demo Script

## Setup

1. Start LangGraph locally.
2. Open LangGraph Studio.
3. Load the graph.
4. Paste in the onboarding sample brief.

## Talk Track

### 1. Frame the use case

"This is a small deployment-readiness copilot. It is meant to turn a vague workflow request into a reviewable plan for piloting an agent safely."

### 2. Walk through the graph

- ingest the brief
- analyze the workflow
- draft a plan
- pause for human review
- either finalize or escalate

### 3. Emphasize human review

"I intentionally added an interrupt before final output because this kind of workflow should not pretend full autonomy is always desirable."

### 4. Emphasize fallback behavior

"If confidence is weak or the reviewer pushes back, the graph escalates instead of bluffing."

### 5. Emphasize observability

"Every run can be traced in LangSmith, and I added a starter eval harness so the repo is not just prompt output without checks."

