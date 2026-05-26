#!/usr/bin/env python3
"""
Example 03: upload a file and create a vector store linked to an agent.

Env: KIMSS_API_KEY, KIMSS_ASSISTANT_ID, KIMSS_UPLOAD_PATH (path to a small file).
"""
from __future__ import annotations

import os
import sys

from kimss import KimssClient


def main() -> None:
    key = (os.environ.get("KIMSS_API_KEY") or "").strip()
    aid = (os.environ.get("KIMSS_ASSISTANT_ID") or "").strip()
    path = (os.environ.get("KIMSS_UPLOAD_PATH") or "").strip()
    if not key or not aid or not path:
        print("Set KIMSS_API_KEY, KIMSS_ASSISTANT_ID, KIMSS_UPLOAD_PATH", file=sys.stderr)
        raise SystemExit(1)
    if not os.path.isfile(path):
        print(f"Not a file: {path}", file=sys.stderr)
        raise SystemExit(2)
    base = (os.environ.get("KIMSS_BASE_URL") or "https://api.kimss.ai").rstrip("/")
    client = KimssClient(api_key=key, base_url=base)
    up = client.files.upload(path)
    print("upload:", up)
    vs = client.vector_stores.create(name="example-store", agent_id=aid)
    print("vector_store:", vs)


if __name__ == "__main__":
    main()
