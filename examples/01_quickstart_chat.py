#!/usr/bin/env python3
"""Example 01: quickstart chat (env: KIMSS_API_KEY, KIMSS_ASSISTANT_ID)."""
from __future__ import annotations

import os
import sys

from kimss import KimssClient


def main() -> None:
    key = (os.environ.get("KIMSS_API_KEY") or "").strip()
    aid = (os.environ.get("KIMSS_ASSISTANT_ID") or "").strip()
    if not key or not aid:
        print("Set KIMSS_API_KEY and KIMSS_ASSISTANT_ID", file=sys.stderr)
        raise SystemExit(1)
    base = (os.environ.get("KIMSS_BASE_URL") or "https://api.kimss.ai").rstrip("/")
    client = KimssClient(api_key=key, base_url=base)
    agent = client.get_agent(aid)
    result = agent.query("Hello from the Kimss Python SDK example.")
    print(result)


if __name__ == "__main__":
    main()
