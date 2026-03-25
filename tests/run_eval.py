from __future__ import annotations

import json
import uuid
from pathlib import Path

from langgraph.types import Command

from agent_deployment_readiness_lab.graph import graph


def load_cases() -> list[dict]:
    path = Path(__file__).with_name("eval_cases.jsonl")
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def invoke_case(brief: str) -> str:
    config = {"configurable": {"thread_id": f"eval-{uuid.uuid4()}"}}
    result = graph.invoke({"brief": brief}, config=config, version="v2")

    if getattr(result, "interrupts", None):
        resumed = graph.invoke(
            Command(
                resume={
                    "approved": True,
                    "notes": "Auto-approved during eval run.",
                }
            ),
            config=config,
            version="v2",
        )
        return resumed.value["final_output"]

    return result.value["final_output"]


def main():
    cases = load_cases()
    passed = 0

    for case in cases:
        output = invoke_case(case["brief"])
        missing = [section for section in case["expected_sections"] if section not in output]
        if missing:
            print(f"FAIL {case['name']}: missing {missing}")
            continue
        passed += 1
        print(f"PASS {case['name']}")

    print(f"{passed}/{len(cases)} cases passed")


if __name__ == "__main__":
    main()

