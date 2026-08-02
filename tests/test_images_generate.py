"""Tests for client.images.generate (POST /v1/images/generations)."""
from __future__ import annotations

import json

import pytest
import responses

from kimss import KimssClient


@responses.activate
def test_images_generate_returns_data() -> None:
    responses.add(
        responses.POST,
        "https://api.kimss.ai/v1/images/generations",
        json={
            "id": "img-abc",
            "created": 1754150000,
            "model": "kimss-gpt-image-2",
            "data": [{"b64_json": "aGVsbG8="}],
            "usage": {"images": 1, "billing": "per_image_not_token_metered"},
        },
        status=200,
    )
    client = KimssClient(api_key="k", base_url="https://api.kimss.ai", session=None)
    out = client.images.generate("a gateway diagram", size="1024x1024", quality="high", n=1)
    assert out["model"] == "kimss-gpt-image-2"
    assert out["data"][0]["b64_json"] == "aGVsbG8="
    body = responses.calls[0].request.body
    payload = json.loads(body if isinstance(body, str) else body.decode())
    assert payload["prompt"] == "a gateway diagram"
    assert payload["size"] == "1024x1024"
    assert payload["quality"] == "high"
    assert payload["n"] == 1
    assert "model" not in payload


@responses.activate
def test_images_generate_passes_model() -> None:
    responses.add(
        responses.POST,
        "https://api.kimss.ai/v1/images/generations",
        json={"data": [{"b64_json": "eA=="}]},
        status=200,
    )
    client = KimssClient(api_key="k", base_url="https://api.kimss.ai", session=None)
    client.images.generate("x", model="gpt-image-2")
    body = responses.calls[0].request.body
    payload = json.loads(body if isinstance(body, str) else body.decode())
    assert payload["model"] == "gpt-image-2"


def test_images_generate_requires_prompt() -> None:
    client = KimssClient(api_key="k", base_url="https://api.kimss.ai", session=None)
    with pytest.raises(ValueError, match="non-empty prompt"):
        client.images.generate("   ")
