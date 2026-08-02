#!/usr/bin/env python3
"""Example 07: image generation via the Kimss gateway (env: KIMSS_API_KEY).

Requires image generation to be enabled on your Kimss environment
(a 404 feature_disabled response means it is not enabled yet).
"""
from __future__ import annotations

import base64
import os
import sys

from kimss import KimssClient


def main() -> None:
    key = (os.environ.get("KIMSS_API_KEY") or "").strip()
    if not key:
        print("Set KIMSS_API_KEY", file=sys.stderr)
        raise SystemExit(1)
    base = (os.environ.get("KIMSS_BASE_URL") or "https://api.kimss.ai").rstrip("/")
    client = KimssClient(api_key=key, base_url=base)
    res = client.images.generate(
        "A minimal dark-indigo tech illustration of one governed API gateway "
        "in front of many AI agent nodes, clean editorial style",
        size="1024x1024",
        quality="medium",
    )
    item = (res.get("data") or [{}])[0]
    b64 = item.get("b64_json")
    if not b64:
        print("no image data returned:", res, file=sys.stderr)
        raise SystemExit(1)
    out_path = os.path.abspath("kimss_generated_image.png")
    with open(out_path, "wb") as f:
        f.write(base64.b64decode(b64))
    print("model:", res.get("model"))
    print("saved:", out_path)


if __name__ == "__main__":
    main()
