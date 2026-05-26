"""
MCP tool implementations — thin wrappers around :class:`kimss.client.KimssClient`.

Input JSON schemas (for tests and documentation) are OpenAPI-style object schemas.
"""
from __future__ import annotations

import json
from typing import Any

from kimss.client import KimssClient
from kimss.errors import KimssApiError

# JSON Schema fragments for tool arguments (used by tests and docs).
TOOL_INPUT_SCHEMAS: dict[str, dict[str, Any]] = {
    "kimss_chat": {
        "type": "object",
        "properties": {
            "assistant_id": {"type": "string", "description": "Kimss assistant / agent id"},
            "message": {"type": "string"},
            "thread_id": {"type": "string", "description": "Optional thread to continue"},
        },
        "required": ["assistant_id", "message"],
        "additionalProperties": False,
    },
    "kimss_create_agent": {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "model": {"type": "string"},
            "instructions": {"type": "string"},
            "metadata": {"type": "object"},
            "owner_id": {"type": "string"},
            "tools": {"type": "array"},
            "tenant_id": {"type": "string"},
        },
        "required": ["name"],
        "additionalProperties": False,
    },
    "kimss_run_agent": {
        "type": "object",
        "properties": {
            "assistant_id": {"type": "string"},
            "message": {"type": "string"},
            "thread_id": {"type": "string"},
            "chat_type": {"type": "string", "default": "user_chat"},
        },
        "required": ["assistant_id", "message"],
        "additionalProperties": False,
    },
    "kimss_complete": {
        "type": "object",
        "properties": {
            "model": {"type": "string"},
            "messages": {
                "type": "array",
                "items": {"type": "object"},
                "description": "Chat messages, e.g. [{'role':'user','content':'hi'}]",
            },
            "system": {"type": "string"},
            "max_tokens": {"type": "integer"},
            "temperature": {"type": "number"},
        },
        "required": ["model", "messages"],
        "additionalProperties": False,
    },
    "kimss_upload_file": {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Local filesystem path to upload"},
            "filename": {"type": "string"},
            "content_type": {"type": "string", "default": "application/octet-stream"},
        },
        "required": ["path"],
        "additionalProperties": False,
    },
    "kimss_create_vector_store": {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "agent_id": {
                "type": "string",
                "description": "Link store to agent (replace semantics)",
            },
            "metadata": {"type": "object"},
            "tenant_id": {"type": "string"},
        },
        "required": [],
        "additionalProperties": False,
    },
    "kimss_add_function_to_agent": {
        "type": "object",
        "properties": {
            "agent_id": {"type": "string"},
            "name": {"type": "string"},
            "description": {"type": "string"},
            "parameters": {"type": "object", "description": "JSON Schema for tool parameters"},
        },
        "required": ["agent_id", "name"],
        "additionalProperties": False,
    },
}


def _tool_error_payload(exc: KimssApiError) -> str:
    """Serialize Kimss API errors for MCP tool failures (no secrets)."""
    payload = {
        "kind": "kimss_api_error",
        "http_status": exc.status_code,
        "error_code": exc.error_code,
        "message": str(exc),
        "detail": exc.detail,
    }
    return json.dumps(payload, default=str)


def kimss_chat(
    client: KimssClient,
    assistant_id: str,
    message: str,
    thread_id: str | None = None,
) -> Any:
    return client.chat(assistant_id, message, thread_id=thread_id)


def kimss_create_agent(
    client: KimssClient,
    name: str,
    model: str | None = None,
    instructions: str | None = None,
    metadata: dict[str, Any] | None = None,
    owner_id: str | None = None,
    tools: list[dict[str, Any]] | None = None,
    tenant_id: str | None = None,
) -> Any:
    return client.agents.create(
        name=name,
        model=model,
        instructions=instructions,
        metadata=metadata,
        owner_id=owner_id,
        tools=tools,
        tenant_id=tenant_id,
    )


def kimss_run_agent(
    client: KimssClient,
    assistant_id: str,
    message: str,
    thread_id: str | None = None,
    chat_type: str = "user_chat",
) -> Any:
    return client.agents.run(
        assistant_id,
        message,
        stream=False,
        thread_id=thread_id,
        chat_type=chat_type,
    )


def kimss_complete(
    client: KimssClient,
    model: str,
    messages: list[dict[str, str]],
    system: str | None = None,
    max_tokens: int | None = None,
    temperature: float | None = None,
) -> Any:
    return client.models.create(
        model,
        messages,
        stream=False,
        system=system,
        max_tokens=max_tokens,
        temperature=temperature,
    )


def kimss_upload_file(
    client: KimssClient,
    path: str,
    filename: str | None = None,
    content_type: str = "application/octet-stream",
) -> Any:
    return client.files.upload(path, filename=filename, content_type=content_type)


def kimss_create_vector_store(
    client: KimssClient,
    name: str | None = None,
    agent_id: str | None = None,
    metadata: dict[str, Any] | None = None,
    tenant_id: str | None = None,
) -> Any:
    return client.vector_stores.create(
        name=name,
        agent_id=agent_id,
        metadata=metadata,
        tenant_id=tenant_id,
    )


def kimss_add_function_to_agent(
    client: KimssClient,
    agent_id: str,
    name: str,
    description: str | None = None,
    parameters: dict[str, Any] | None = None,
) -> Any:
    return client.add_function_to_agent(
        agent_id,
        name,
        description=description,
        parameters=parameters,
    )
