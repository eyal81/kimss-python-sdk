"""Tests for client.models.create (completions + prompt alias)."""
from __future__ import annotations

import json

import pytest
import responses

from kimss import KimssClient


@responses.activate
def test_create_with_messages() -> None:
    responses.add(
        responses.POST,
        "https://api.kimss.ai/v1/models/completions",
        json={"res": {"output": "pong"}},
        status=200,
    )
    client = KimssClient(api_key="k", base_url="https://api.kimss.ai", session=None)
    out = client.models.create(
        "gpt-test",
        [{"role": "user", "content": "ping"}],
        stream=False,
    )
    assert out["output"] == "pong"
    body = responses.calls[0].request.body
    assert body is not None
    payload = json.loads(body if isinstance(body, str) else body.decode())
    assert payload["model"] == "gpt-test"
    assert payload["messages"] == [{"role": "user", "content": "ping"}]


@responses.activate
def test_create_prompt_alias_builds_user_message() -> None:
    """Digital Workers may call models.create(prompt=...) like agents.run."""
    responses.add(
        responses.POST,
        "https://api.kimss.ai/v1/models/completions",
        json={"res": {"output": "ok"}},
        status=200,
    )
    client = KimssClient(api_key="k", base_url="https://api.kimss.ai", session=None)
    out = client.models.create(model="gpt-test", prompt="How many runs?", stream=False)
    assert out["output"] == "ok"
    body = responses.calls[0].request.body
    assert body is not None
    payload = json.loads(body if isinstance(body, str) else body.decode())
    assert payload["messages"] == [{"role": "user", "content": "How many runs?"}]
    assert "prompt" not in payload


def test_create_requires_messages_or_prompt() -> None:
    client = KimssClient(api_key="k", base_url="https://api.kimss.ai", session=None)
    with pytest.raises(ValueError, match="messages or a non-empty prompt"):
        client.models.create(model="gpt-test", stream=False)
