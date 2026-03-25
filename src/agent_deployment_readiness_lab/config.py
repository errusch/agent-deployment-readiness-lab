from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache


@dataclass(frozen=True)
class Settings:
    model_name: str
    approval_confidence_threshold: float


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    model_name = os.getenv("AGENT_DEPLOYMENT_MODEL", "openai:gpt-4.1-mini")
    threshold = float(os.getenv("APPROVAL_CONFIDENCE_THRESHOLD", "0.65"))
    return Settings(
        model_name=model_name,
        approval_confidence_threshold=threshold,
    )

