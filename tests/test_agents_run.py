"""Tests for client.agents.run (v1 orchestration)."""
from __future__ import annotations

import json

import pytest
import responses

from kimss import AgentRunResult, KimssClient


@responses.activate
def test_run_positional_returns_agent_run_result_with_text_and_usage() -> None:
    responses.add(
        responses.POST,
        "https://api.kimss.ai/v1/agents/run",
        json={
            "res": {
                "thread_id": "t1",
                "output": "hello",
                "usage": {"total_credits": 1.5},
            }
        },
        status=200,
    )
    client = KimssClient(api_key="k", base_url="https://api.kimss.ai", session=None)
    result = client.agents.run("asst_x", "hi", stream=False)
    assert isinstance(result, AgentRunResult)
    assert result["thread_id"] == "t1"
    assert result.text == "hello"
    assert result.usage.total_credits == 1.5


@responses.activate
def test_run_agent_id_prompt_aliases() -> None:
    responses.add(
        responses.POST,
        "https://api.kimss.ai/v1/agents/run",
        json={"res": {"assistant_response": "ok"}},
        status=200,
    )
    client = KimssClient(api_key="k", base_url="https://api.kimss.ai", session=None)
    result = client.agents.run(agent_id="asst_y", prompt="ping", stream=False)
    assert isinstance(result, AgentRunResult)
    assert result.text == "ok"
    body = responses.calls[0].request.body
    assert body is not None
    payload = json.loads(body if isinstance(body, str) else body.decode())
    assert payload["assistant_id"] == "asst_y"
    assert payload["usr_chat"] == "ping"


@responses.activate
def test_run_tags_and_routing_preference_in_post_body() -> None:
    responses.add(
        responses.POST,
        "https://api.kimss.ai/v1/agents/run",
        json={"res": {"output": "x"}},
        status=200,
    )
    client = KimssClient(api_key="k", base_url="https://api.kimss.ai", session=None)
    client.agents.run(
        "asst_z",
        "q",
        stream=False,
        tags=["enterprise", "demo"],
        routing_preference=" primary ",
    )
    rb = responses.calls[0].request.body
    assert rb is not None
    payload = json.loads(rb if isinstance(rb, str) else rb.decode())
    assert payload["tags"] == ["enterprise", "demo"]
    assert payload["routing_preference"] == "primary"


@responses.activate
def test_run_top_level_total_credits_maps_to_usage() -> None:
    responses.add(
        responses.POST,
        "https://api.kimss.ai/v1/agents/run",
        json={"res": {"output": "done", "total_credits": "2.25"}},
        status=200,
    )
    client = KimssClient(api_key="k", base_url="https://api.kimss.ai", session=None)
    result = client.agents.run("asst_a", "m", stream=False)
    assert isinstance(result, AgentRunResult)
    assert result.usage.total_credits == 2.25


def test_run_requires_assistant_or_agent() -> None:
    client = KimssClient(api_key="k", base_url="https://api.kimss.ai", session=None)
    with pytest.raises(ValueError, match="assistant_id or agent_id"):
        client.agents.run(prompt="only prompt", stream=False)


def test_run_requires_message_or_prompt() -> None:
    client = KimssClient(api_key="k", base_url="https://api.kimss.ai", session=None)
    with pytest.raises(ValueError, match="message or prompt"):
        client.agents.run("asst_x", "", stream=False)
