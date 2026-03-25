# Current Limitations

## Runtime

- Uses in-memory checkpointing for local development only
- Assumes one configured model provider
- Uses structured LLM calls rather than a richer tool-execution loop
- Includes an offline demo mode that validates the workflow shape but does not represent real model behavior

## UX

- No inbox or web UI yet
- Interrupt responses are handled through LangGraph runtime tooling rather than a custom reviewer surface

## Evaluation

- The starter eval harness checks for section presence, not output quality
- No rubric scoring yet
- No trajectory-level evaluation yet

## Security

- No authentication or permission model
- No PII handling policy
- No audit trail beyond LangSmith tracing if enabled

## What I Would Add Next

- persistent checkpointer
- authenticated review surface
- richer business tools and retrieval
- stronger LangSmith evals
- output persistence and comparison across runs
