#!/usr/bin/env python3
"""DEPRECATED inference demo — prefer examples/00_gateway_proxy.py.

Control-plane create may still be useful; do not use agents.run for new apps.
"""
from __future__ import annotations

import os
import sys
import warnings

from kimss import KimssClient


def main() -> None:
    warnings.warn(
        "02_create_agent.py uses deprecated agents.run; "
        "prefer OpenAI gateway (00_gateway_proxy.py)",
        DeprecationWarning,
        stacklevel=1,
    )
    key = (os.environ.get("KIMSS_API_KEY") or "").strip()
    if not key:
        print("Set KIMSS_API_KEY", file=sys.stderr)
        raise SystemExit(1)
    base = (os.environ.get("KIMSS_BASE_URL") or "https://api.kimss.ai").rstrip("/")
    client = KimssClient(api_key=key, base_url=base)
    created = client.agents.create(
        name="SDK Example Agent",
        instructions="You are a concise helper.",
    )
    print("created:", created)
    assistant_id = (created or {}).get("assistant_id") or (created or {}).get("id")
    if not assistant_id:
        print("No assistant_id in response; check API key scopes.", file=sys.stderr)
        raise SystemExit(2)
    run = client.agents.run(str(assistant_id), "Say hello in one sentence.", stream=False)
    print("run:", run)


if __name__ == "__main__":
    main()
