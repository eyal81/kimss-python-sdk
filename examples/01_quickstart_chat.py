#!/usr/bin/env python3
"""DEPRECATED pattern — prefer examples/00_gateway_proxy.py (OpenAI base_url + Agent-Id).

This script still calls KimssClient.query for backward compatibility only.
"""
from __future__ import annotations

import os
import sys
import warnings

from kimss import KimssClient


def main() -> None:
    warnings.warn(
        "01_quickstart_chat.py uses deprecated KimssClient inference; see 00_gateway_proxy.py",
        DeprecationWarning,
        stacklevel=1,
    )
    key = (os.environ.get("KIMSS_API_KEY") or "").strip()
    aid = (os.environ.get("KIMSS_ASSISTANT_ID") or "").strip()
    if not key or not aid:
        print(
            "Set KIMSS_API_KEY and KIMSS_ASSISTANT_ID (or use 00_gateway_proxy.py)",
            file=sys.stderr,
        )
        raise SystemExit(1)
    base = (os.environ.get("KIMSS_BASE_URL") or "https://api.kimss.ai").rstrip("/")
    client = KimssClient(api_key=key, base_url=base)
    agent = client.get_agent(aid)
    result = agent.query("Hello from the Kimss Python SDK example.")
    print(result)


if __name__ == "__main__":
    main()
