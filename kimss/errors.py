"""Typed HTTP errors for the Kimss Python SDK."""

from __future__ import annotations

from typing import Any, Dict, Optional

import requests


class KimssApiError(Exception):
    """Base class for Kimss API failures with the originating response."""

    def __init__(
        self,
        message: str,
        *,
        response: requests.Response,
        error_code: Optional[str] = None,
        detail: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message)
        self.response = response
        self.status_code = response.status_code
        self.error_code = error_code
        self.detail = detail or {}


class KimssCreditExhausted(KimssApiError):
    """Monthly credit pool or individual trial cap exhausted (HTTP 429)."""


class KimssSubscriptionRequired(KimssApiError):
    """Workspace lacks paid entitlement (HTTP 403)."""


class KimssRateLimited(KimssApiError):
    """Rate limit exceeded (HTTP 429)."""


def _detail_dict(response: requests.Response) -> Optional[Dict[str, Any]]:
    try:
        data = response.json()
    except Exception:
        return None
    d = data.get("detail")
    if isinstance(d, dict):
        return d
    details = data.get("details")
    if isinstance(details, dict):
        nested = details.get("detail")
        if isinstance(nested, dict):
            return nested
    if isinstance(data.get("code"), str):
        out: Dict[str, Any] = {"error": data.get("code")}
        if isinstance(data.get("message"), str):
            out["message"] = data.get("message")
        if isinstance(details, dict):
            out["details"] = details
        return out
    return None


def raise_for_kimss_error(response: requests.Response) -> None:
    """Raise typed Kimss errors for known envelopes; otherwise ``HTTPError``."""
    if response.status_code < 400:
        return
    detail = _detail_dict(response)
    err = str((detail or {}).get("error") or "").strip()

    if response.status_code == 403 and err == "subscription_required":
        msg = str((detail or {}).get("message") or "subscription_required")
        raise KimssSubscriptionRequired(msg, response=response, error_code=err, detail=detail)

    if response.status_code == 429:
        if err in ("credit_pool_exhausted", "individual_free_trial_exhausted", "credit_policy_blocked"):
            msg = str((detail or {}).get("message") or err or "credit exhausted")
            raise KimssCreditExhausted(msg, response=response, error_code=err or None, detail=detail)
        if err in ("rate_limit_exceeded", "rate_limited"):
            msg = str((detail or {}).get("message") or "rate_limit_exceeded")
            raise KimssRateLimited(msg, response=response, error_code=err, detail=detail)

    response.raise_for_status()
