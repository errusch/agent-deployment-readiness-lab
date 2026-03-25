from __future__ import annotations

import argparse
import json
import os
import sys
import uuid
from pathlib import Path

from dotenv import load_dotenv
from langgraph.types import Command

from .graph import graph


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the Agent Deployment Readiness Lab graph from the terminal.",
    )
    parser.add_argument(
        "--brief",
        help="Workflow brief text to process.",
    )
    parser.add_argument(
        "--brief-file",
        help="Path to a text file containing the workflow brief.",
    )
    parser.add_argument(
        "--thread-id",
        help="Optional LangGraph thread ID. Defaults to a random ID.",
    )
    parser.add_argument(
        "--auto-approve",
        action="store_true",
        help="Automatically approve the review step for demos and evals.",
    )
    parser.add_argument(
        "--approval-notes",
        default="Looks good. Keep the rollout conservative.",
        help="Notes to send when --auto-approve is used.",
    )
    parser.add_argument(
        "--output-file",
        help="Optional path to write the final markdown output.",
    )
    parser.add_argument(
        "--show-interrupt",
        action="store_true",
        help="Print the interrupt payload before resuming.",
    )
    return parser


def load_brief(args: argparse.Namespace) -> str:
    if args.brief:
        return args.brief.strip()
    if args.brief_file:
        return Path(args.brief_file).read_text().strip()
    raise SystemExit("Provide --brief or --brief-file.")


def ensure_model_env() -> None:
    if os.getenv("OPENAI_API_KEY"):
        return
    raise SystemExit(
        "OPENAI_API_KEY is not set. Copy .env.example to .env, add your key, then rerun.",
    )


def extract_interrupt_payload(result) -> object | None:
    interrupts = getattr(result, "interrupts", None)
    if interrupts:
        first = interrupts[0]
        return getattr(first, "value", first)

    value = getattr(result, "value", None)
    if isinstance(value, dict):
        raw_interrupt = value.get("__interrupt__")
        if raw_interrupt:
            first = raw_interrupt[0]
            return getattr(first, "value", first)

    return None


def extract_final_output(result) -> str:
    value = getattr(result, "value", result)
    if isinstance(value, dict) and "final_output" in value:
        return value["final_output"]
    raise SystemExit("Graph completed without a final_output field.")


def write_output(text: str, output_file: str | None) -> None:
    if not output_file:
        print(text)
        return

    path = Path(output_file)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    print(f"Wrote final output to {path}")


def main() -> int:
    load_dotenv()
    parser = build_parser()
    args = parser.parse_args()
    ensure_model_env()

    brief = load_brief(args)
    thread_id = args.thread_id or f"agent-readiness-{uuid.uuid4()}"
    config = {"configurable": {"thread_id": thread_id}}

    result = graph.invoke({"brief": brief}, config=config)
    interrupt_payload = extract_interrupt_payload(result)

    if interrupt_payload is not None and not args.auto_approve:
        print("Graph paused for review.")
        print("Use --auto-approve for a one-shot demo run, or resume manually in LangGraph Studio.")
        if args.show_interrupt:
            print(json.dumps(interrupt_payload, indent=2, default=str))
        return 0

    if interrupt_payload is not None:
        if args.show_interrupt:
            print(json.dumps(interrupt_payload, indent=2, default=str))
        result = graph.invoke(
            Command(
                resume={
                    "approved": True,
                    "notes": args.approval_notes,
                }
            ),
            config=config,
        )

    final_output = extract_final_output(result)
    write_output(final_output, args.output_file)
    return 0


if __name__ == "__main__":
    sys.exit(main())

