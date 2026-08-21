#!/usr/bin/env python3
"""Anthropic SDK drop-in through Kimss dual-listener (POST /v1/messages).

Env:
  KIMSS_WORKSPACE_KEY or KIMSS_API_KEY or ANTHROPIC_API_KEY
  KIMSS_AGENT_ID
  KIMSS_MODEL
  ANTHROPIC_BASE_URL or KIMSS_BASE_URL (optional; default https://api.kimss.ai)
"""
from __future__ import annotations

import os
import sys

from anthropic import Anthropic


def main() -> None:
    key = (
        os.environ.get("KIMSS_WORKSPACE_KEY")
        or os.environ.get("KIMSS_API_KEY")
        or os.environ.get("ANTHROPIC_API_KEY")
        or ""
    ).strip()
    agent_id = (os.environ.get("KIMSS_AGENT_ID") or "").strip()
    model = (os.environ.get("KIMSS_MODEL") or "").strip()
    if not key or not agent_id or not model:
        print("Set KIMSS_WORKSPACE_KEY, KIMSS_AGENT_ID, and KIMSS_MODEL.", file=sys.stderr)
        raise SystemExit(1)
    base = (
        os.environ.get("ANTHROPIC_BASE_URL")
        or os.environ.get("KIMSS_BASE_URL")
        or "https://api.kimss.ai"
    ).rstrip("/")
    if base.endswith("/v1"):
        base = base[: -len("/v1")]
    name = (os.environ.get("KIMSS_AGENT_NAME") or "Gateway Proxy Agent").strip()

    client = Anthropic(base_url=base, api_key=key)
    resp = client.messages.create(
        model=model,
        max_tokens=256,
        messages=[{"role": "user", "content": "Execute database audit."}],
        extra_headers={
            "X-Kimss-Agent-Id": agent_id,
            "X-Kimss-Agent-Name": name,
        },
    )
    text = "".join(b.text for b in resp.content if getattr(b, "type", "") == "text")
    print(text)


if __name__ == "__main__":
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except ImportError:
        pass
    main()
