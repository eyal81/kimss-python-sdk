"""Tests for KimssClient request headers and retry behavior (no live API)."""
from __future__ import annotations

import json

import responses
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from kimss import KimssClient


@responses.activate
def test_api_key_sets_x_kimss_key() -> None:
    responses.add(
        responses.POST,
        "https://api.kimss.ai/assistant_chat/",
        json={"res": {"ok": True}},
        status=200,
    )
    client = KimssClient(api_key="kimss_test", base_url="https://api.kimss.ai", session=None)
    client.chat("asst_x", "hi")
    assert len(responses.calls) == 1
    assert responses.calls[0].request.headers.get("X-Kimss-Key") == "kimss_test"


@responses.activate
def test_workspace_id_header_and_tenant_id_body() -> None:
    responses.add(
        responses.POST,
        "https://api.kimss.ai/assistant_chat/",
        json={"res": {}},
        status=200,
    )
    client = KimssClient(
        api_key="k",
        base_url="https://api.kimss.ai",
        workspace_id="ws1",
        session=None,
    )
    client.chat("asst_x", "hi")
    body = responses.calls[0].request.body
    assert responses.calls[0].request.headers.get("X-Workspace-ID") == "ws1"
    assert body is not None
    raw = body if isinstance(body, str) else body.decode()
    payload = json.loads(raw)
    assert payload.get("tenant_id") == "ws1"


def test_default_retry_does_not_include_429() -> None:
    client = KimssClient(api_key="k", base_url="https://api.kimss.ai", session=None)
    adapter = client._session.get_adapter("https://")
    assert isinstance(adapter, HTTPAdapter)
    r = adapter.max_retries  # type: ignore[attr-defined]
    assert isinstance(r, Retry)
    assert 429 not in r.status_forcelist
