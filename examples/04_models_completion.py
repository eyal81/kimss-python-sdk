#!/usr/bin/env python3
"""Example 04: model completions — non-stream and stream (env: KIMSS_API_KEY, KIMSS_MODEL)."""
from __future__ import annotations

import os
import sys

from kimss import KimssClient


def main() -> None:
    key = (os.environ.get("KIMSS_API_KEY") or "").strip()
    model = (os.environ.get("KIMSS_MODEL") or "").strip()
    if not key or not model:
        print(
            "Set KIMSS_API_KEY and KIMSS_MODEL (deployment name in your workspace)",
            file=sys.stderr,
        )
        raise SystemExit(1)
    base = (os.environ.get("KIMSS_BASE_URL") or "https://api.kimss.ai").rstrip("/")
    client = KimssClient(api_key=key, base_url=base)
    res = client.models.create(
        model,
        [{"role": "user", "content": "Reply with exactly: pong"}],
        stream=False,
    )
    print("non-stream:", res)
    gen = client.models.create(
        model,
        [{"role": "user", "content": "Count 1 2 3"}],
        stream=True,
    )
    chunks = []
    for obj in gen:
        chunks.append(obj)
    print("stream chunks:", len(chunks))


if __name__ == "__main__":
    main()
