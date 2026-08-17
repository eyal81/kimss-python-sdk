"""Kimss Python SDK – integration layer for the Kimss Secure AI Gateway."""
from .client import Agent, AgentRunResult, AgentRunUsage, KimssClient
from .environment import KimssEnv, current_env, env_label, is_staging, redis_cache_namespace_infix
from .errors import (
    KimssApiError,
    KimssCreditExhausted,
    KimssGovernedRequestsExhausted,
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
    "KimssGovernedRequestsExhausted",
    "KimssSubscriptionRequired",
    "KimssRateLimited",
    "raise_for_kimss_error",
    "BeforeRequestHook",
    "PresidioRedactor",
]
