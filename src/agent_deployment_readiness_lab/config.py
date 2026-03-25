from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    model_name: str
    approval_confidence_threshold: float
    demo_mode: bool


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    load_dotenv()
    model_name = os.getenv("AGENT_DEPLOYMENT_MODEL", "openai:gpt-4.1-mini")
    threshold = float(os.getenv("APPROVAL_CONFIDENCE_THRESHOLD", "0.65"))
    demo_mode = os.getenv("AGENT_DEPLOYMENT_DEMO_MODE", "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
    return Settings(
        model_name=model_name,
        approval_confidence_threshold=threshold,
        demo_mode=demo_mode,
    )
