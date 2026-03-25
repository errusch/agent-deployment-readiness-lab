import argparse

import pytest

from agent_deployment_readiness_lab.cli import ensure_model_env, load_brief, load_input_state


def test_load_brief_from_argument():
    args = argparse.Namespace(brief="  hello world  ", brief_file=None, request_file=None)
    assert load_brief(args) == "hello world"


def test_load_brief_requires_input():
    args = argparse.Namespace(brief=None, brief_file=None, request_file=None)
    with pytest.raises(SystemExit):
        load_brief(args)


def test_ensure_model_env_requires_openai_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("AGENT_DEPLOYMENT_DEMO_MODE", raising=False)
    with pytest.raises(SystemExit):
        ensure_model_env()


def test_ensure_model_env_allows_demo_mode(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("AGENT_DEPLOYMENT_DEMO_MODE", "true")
    ensure_model_env()


def test_load_input_state_from_request_file(tmp_path):
    request_file = tmp_path / "request.json"
    request_file.write_text(
        """
        {
          "request_id": "onb-001",
          "workflow_type": "onboarding_ops",
          "subject": "New client onboarding request",
          "thread": [
            {
              "from": "client",
              "timestamp": "2026-03-25T09:00:00Z",
              "body": "Customer name: Acme\\nImplementation goal: Launch a pilot\\nTimeline: April 15\\nPrimary contact: Sarah Kim"
            }
          ],
          "metadata": {
            "customer_name": "Acme"
          }
        }
        """.strip()
    )
    args = argparse.Namespace(
        brief=None,
        brief_file=None,
        request_file=str(request_file),
        schema_file=None,
    )
    state = load_input_state(args)
    assert state["source_mode"] == "request_file"
    assert state["request_packet"]["request_id"] == "onb-001"


def test_load_input_state_rejects_invalid_json(tmp_path):
    request_file = tmp_path / "bad.json"
    request_file.write_text("{not json}")
    args = argparse.Namespace(
        brief=None,
        brief_file=None,
        request_file=str(request_file),
        schema_file=None,
    )
    with pytest.raises(SystemExit, match="not valid JSON"):
        load_input_state(args)
