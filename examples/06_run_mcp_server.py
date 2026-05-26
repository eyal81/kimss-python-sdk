#!/usr/bin/env python3
"""
Example 06: run the MCP server locally (stdio — blocks; use Ctrl+C).

Same as: ``python -m kimss.mcp`` or ``kimss-mcp-server`` after ``pip install 'kimss[mcp]'``.

Requires: KIMSS_API_KEY
"""
from __future__ import annotations

import os

from kimss.mcp.server import main

if __name__ == "__main__":
    if not (os.environ.get("KIMSS_API_KEY") or "").strip():
        raise SystemExit("Set KIMSS_API_KEY before running the MCP server.")
    main()
