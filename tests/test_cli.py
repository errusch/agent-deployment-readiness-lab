import argparse

import pytest

from agent_deployment_readiness_lab.cli import ensure_model_env, load_brief


def test_load_brief_from_argument():
    args = argparse.Namespace(brief="  hello world  ", brief_file=None)
    assert load_brief(args) == "hello world"


def test_load_brief_requires_input():
    args = argparse.Namespace(brief=None, brief_file=None)
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

