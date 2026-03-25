# Runtime Evidence

This repo is backed by real LangSmith traces, not just static sample markdown.

## LangSmith Project

- Project: [agent-deployment-readiness-lab](https://smith.langchain.com/o/1e63a055-b03f-4fb3-93ef-80f724ccd7bb/projects/p/bed07692-191d-466e-a4e7-b5f4f164c905)

## Representative Trace

- Example trace from a live `gpt-5.4-mini` onboarding run: [review and finalize flow](https://smith.langchain.com/o/1e63a055-b03f-4fb3-93ef-80f724ccd7bb/projects/p/bed07692-191d-466e-a4e7-b5f4f164c905/r/019d25aa-b6c1-7113-bfa1-feb20d11f163?trace_id=019d25aa-b6bf-7881-b538-f4adb3de5812&start_time=2026-03-25T15:43:58.143700)

## Notes

- These LangSmith links are in the project owner's workspace and may require access.
- The intended public proof pattern for this repo is:
  - inspect the sample outputs in `examples/sample_outputs/`
  - run the graph locally on a sample brief
  - review the trace in LangSmith to inspect interrupt handling, final output, and control flow
- If this repo is shared more broadly, the next step would be to publish one or two selected traces or add screenshots from LangSmith to the README.
