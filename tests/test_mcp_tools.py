"""MCP tool schemas and server bootstrap (no live Kimss API)."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import requests

from kimss.errors import KimssCreditExhausted
from kimss.mcp.tools import TOOL_INPUT_SCHEMAS, _tool_error_payload


def _validate_object_schema(schema: dict[str, Any], payload: dict[str, Any]) -> None:
    assert schema.get("type") == "object"
    for key in schema.get("required") or []:
        assert key in payload, f"missing required {key}"
    if schema.get("additionalProperties") is False:
        allowed = set((schema.get("properties") or {}).keys())
        for k in payload:
            assert k in allowed, f"extra key {k}"


def test_tool_schemas_accept_sample_payloads() -> None:
    samples = {
        "kimss_chat": {"assistant_id": "asst_1", "message": "hi"},
        "kimss_create_agent": {"name": "Agent A"},
        "kimss_run_agent": {"assistant_id": "asst_1", "message": "run"},
        "kimss_complete": {
            "model": "gpt-4",
            "messages": [{"role": "user", "content": "x"}],
        },
        "kimss_upload_file": {"path": "/tmp/x.txt"},
        "kimss_create_vector_store": {},
        "kimss_add_function_to_agent": {"agent_id": "asst_1", "name": "fn1"},
    }
    for name, payload in samples.items():
        _validate_object_schema(TOOL_INPUT_SCHEMAS[name], payload)


def test_tool_error_payload_shape() -> None:
    r = requests.Response()
    r.status_code = 429
    r._content = b"{}"
    exc = KimssCreditExhausted(
        "out",
        response=r,
        error_code="credit_pool_exhausted",
        detail={"a": 1},
    )
    s = _tool_error_payload(exc)
    d = json.loads(s)
    assert d["kind"] == "kimss_api_error"
    assert d["error_code"] == "credit_pool_exhausted"


def test_mcp_server_exits_without_api_key() -> None:
    root = Path(__file__).resolve().parents[1]
    env = os.environ.copy()
    env.pop("KIMSS_API_KEY", None)
    env["PYTHONPATH"] = str(root)
    proc = subprocess.run(
        [sys.executable, "-m", "kimss.mcp.server"],
        cwd=str(root),
        env=env,
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert proc.returncode == 1
    assert "KIMSS_API_KEY" in (proc.stderr or "")
