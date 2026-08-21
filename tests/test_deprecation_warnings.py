"""DeprecationWarnings for inference wrappers (gateway-first 2.1.0)."""
from __future__ import annotations

import warnings

import pytest
import responses

from kimss import KimssClient


@pytest.fixture
def client() -> KimssClient:
    return KimssClient(api_key="kimss_test", base_url="https://api.kimss.ai")


@responses.activate
def test_agents_run_emits_deprecation(client: KimssClient) -> None:
    responses.add(
        responses.POST,
        "https://api.kimss.ai/v1/agents/run",
        json={"res": {"text": "ok", "thread_id": "t1"}},
        status=200,
    )
    with pytest.warns(DeprecationWarning, match="deprecated"):
        client.agents.run("asst_1", "hi", stream=False)


@responses.activate
def test_chat_emits_deprecation(client: KimssClient) -> None:
    responses.add(
        responses.POST,
        "https://api.kimss.ai/v1/agents/run",
        json={"res": {"text": "ok", "thread_id": "t1"}},
        status=200,
    )
    with pytest.warns(DeprecationWarning, match="deprecated"):
        client.chat("asst_1", "hi")


@responses.activate
def test_models_create_emits_deprecation(client: KimssClient) -> None:
    responses.add(
        responses.POST,
        "https://api.kimss.ai/v1/models/completions",
        json={"res": {"choices": [{"message": {"content": "ok"}}]}},
        status=200,
    )
    with pytest.warns(DeprecationWarning, match="deprecated"):
        client.models.create("m1", messages=[{"role": "user", "content": "hi"}])


def test_inference_deprecation_constant_present() -> None:
    # Import side-effect free check that module defines the shared message.
    from kimss import client as client_mod

    assert "OpenAI" in client_mod._INFERENCE_DEPRECATION
    assert "api.kimss.ai/v1" in client_mod._INFERENCE_DEPRECATION


# Silence unrelated DeprecationWarning noise in this module when collecting
warnings.filterwarnings("default", category=DeprecationWarning)
