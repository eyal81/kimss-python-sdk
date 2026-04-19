"""
Client-side / SDK mirror of Kimss deployment environment detection.

Uses the same env vars as the API (`KIMSS_ENV`, `KIMSS_ENV_NAME`) when running
tools or tests that share process env with the backend. For HTTP-only clients,
read `environment` from `GET /api/v1/whoami` instead.
"""
from __future__ import annotations

import os
from enum import Enum
from functools import lru_cache


class KimssEnv(str, Enum):
    PROD = "PROD"
    STAGING = "STAGING"


@lru_cache(maxsize=1)
def current_env() -> KimssEnv:
    raw = (os.getenv("KIMSS_ENV") or os.getenv("KIMSS_ENV_NAME") or "PROD").strip().upper()
    if raw == "STAGING":
        return KimssEnv.STAGING
    return KimssEnv.PROD


def is_staging() -> bool:
    return current_env() is KimssEnv.STAGING


def env_label() -> str:
    return current_env().value


def redis_cache_namespace_infix() -> str:
    """Non-empty only in STAGING (legacy prod Redis key shape unchanged)."""
    return "staging:" if is_staging() else ""
