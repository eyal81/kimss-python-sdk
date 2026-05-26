"""Tests for error mapping from API JSON to typed exceptions."""
from __future__ import annotations

import pytest
import requests

from kimss.errors import (
    KimssCreditExhausted,
    KimssRateLimited,
    KimssSubscriptionRequired,
    raise_for_kimss_error,
)


def _resp(status: int, json_body: dict) -> requests.Response:
    r = requests.Response()
    r.status_code = status
    r.headers["Content-Type"] = "application/json"
    r._content = __import__("json").dumps(json_body).encode()
    return r


def test_subscription_required_403() -> None:
    r = _resp(
        403,
        {"detail": {"error": "subscription_required", "message": "Please upgrade"}},
    )
    with pytest.raises(KimssSubscriptionRequired) as ei:
        raise_for_kimss_error(r)
    assert ei.value.error_code == "subscription_required"


def test_credit_pool_exhausted_429() -> None:
    r = _resp(
        429,
        {"detail": {"error": "credit_pool_exhausted", "message": "no credits"}},
    )
    with pytest.raises(KimssCreditExhausted) as ei:
        raise_for_kimss_error(r)
    assert ei.value.error_code == "credit_pool_exhausted"


def test_rate_limit_exceeded_429() -> None:
    r = _resp(
        429,
        {"detail": {"error": "rate_limit_exceeded", "message": "slow down"}},
    )
    with pytest.raises(KimssRateLimited) as ei:
        raise_for_kimss_error(r)
    assert ei.value.error_code == "rate_limit_exceeded"


def test_unknown_429_http_error() -> None:
    r = _resp(429, {"detail": {"error": "other", "message": "x"}})
    with pytest.raises(requests.HTTPError):
        raise_for_kimss_error(r)
