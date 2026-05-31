"""Kimss Python SDK – lightweight client for Kimss conversational AI API."""
from .client import Agent, AgentRunResult, AgentRunUsage, KimssClient
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
    "AgentRunResult",
    "AgentRunUsage",
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
