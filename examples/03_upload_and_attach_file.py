#!/usr/bin/env python3
"""
Example 03: upload an ephemeral file for model completions.

Kimss does not host RAG or vector stores. Retrieve on your side and pass
augmented messages through the gateway. POST /v1/files/upload is a short-lived
attachment store for completions, not a knowledge base.

Env: KIMSS_API_KEY, KIMSS_UPLOAD_PATH (path to a small file).
"""
from __future__ import annotations

import os
import sys

from kimss import KimssClient


def main() -> None:
    key = (os.environ.get("KIMSS_API_KEY") or "").strip()
    path = (os.environ.get("KIMSS_UPLOAD_PATH") or "").strip()
    if not key or not path:
        print("Set KIMSS_API_KEY, KIMSS_UPLOAD_PATH", file=sys.stderr)
        raise SystemExit(1)
    if not os.path.isfile(path):
        print(f"Not a file: {path}", file=sys.stderr)
        raise SystemExit(2)
    base = (os.environ.get("KIMSS_BASE_URL") or "https://api.kimss.ai").rstrip("/")
    client = KimssClient(api_key=key, base_url=base)
    up = client.files.upload(path)
    print("upload:", up)


if __name__ == "__main__":
    main()
