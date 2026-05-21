"""Kimss Python SDK – lightweight client for Kimss conversational AI API."""
from .client import KimssClient, Agent
from .environment import KimssEnv, current_env, env_label, is_staging, redis_cache_namespace_infix
from .errors import (
    KimssApiError,
    KimssCreditExhausted,
    KimssRateLimited,
    KimssSubscriptionRequired,
    raise_for_kimss_error,
)
from .privacy import BeforeRequestHook, PresidioRedactor

__all__ = [
    "KimssClient",
    "Agent",
    "KimssEnv",
    "current_env",
    "env_label",
    "is_staging",
    "redis_cache_namespace_infix",
    "KimssApiError",
    "KimssCreditExhausted",
    "KimssSubscriptionRequired",
    "KimssRateLimited",
    "raise_for_kimss_error",
    "BeforeRequestHook",
    "PresidioRedactor",
]
