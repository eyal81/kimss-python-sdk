#!/usr/bin/env python3
"""Example 05: handle typed Kimss errors (no real API call unless you set KIMSS_API_KEY)."""
from __future__ import annotations

import os

import requests

from kimss import KimssClient
from kimss.errors import (
    KimssApiError,
    KimssCreditExhausted,
    KimssRateLimited,
    KimssSubscriptionRequired,
    raise_for_kimss_error,
)


def demo_raise_for_status() -> None:
    """Demonstrate mapping without calling Kimss (uses synthetic Response)."""
    r = requests.Response()
    r.status_code = 403
    r._content = b'{"detail":{"error":"subscription_required","message":"upgrade"}}'
    r.headers["Content-Type"] = "application/json"
    try:
        raise_for_kimss_error(r)
    except KimssSubscriptionRequired as e:
        print("caught KimssSubscriptionRequired:", e.error_code, e.detail)


def main() -> None:
    demo_raise_for_status()
    key = (os.environ.get("KIMSS_API_KEY") or "").strip()
    if not key:
        print("(Optional) Set KIMSS_API_KEY to exercise live errors against the API.")
        return
    base = (os.environ.get("KIMSS_BASE_URL") or "https://api.kimss.ai").rstrip("/")
    client = KimssClient(api_key=key, base_url=base)
    try:
        client.chat("invalid_assistant_id_xyz", "hi")
    except KimssCreditExhausted as e:
        print("credit exhausted:", e)
    except KimssRateLimited as e:
        print("rate limited:", e)
    except KimssSubscriptionRequired as e:
        print("subscription required:", e)
    except KimssApiError as e:
        print("kimss api:", e.status_code, e.error_code)
    except Exception as e:
        print("other:", e)


if __name__ == "__main__":
    main()
