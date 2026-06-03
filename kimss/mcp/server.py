"""
Kimss MCP server (stdio). Install: ``pip install 'kimss[mcp]'`` — run: ``kimss-mcp-server``.

Environment:

- ``KIMSS_API_KEY`` (required): long-lived API key from Kimss Developer Settings.
- ``KIMSS_BASE_URL`` (optional): default ``https://api.kimss.ai``.
- ``KIMSS_WORKSPACE_ID`` (optional): sent as ``X-Workspace-ID`` / ``tenant_id``.

Never log the API key.
"""
from __future__ import annotations

import asyncio
import os
import sys
from typing import Any

from kimss import KimssClient
from kimss.errors import KimssApiError
from kimss.mcp import tools as mcp_tools

_client: KimssClient | None = None


def _get_client() -> KimssClient:
    if _client is None:
        raise RuntimeError("KimssClient not configured")
    return _client


def _run_tool(fn: Any, /, **kwargs: Any) -> Any:
    try:
        return fn(_get_client(), **kwargs)
    except KimssApiError as e:
        raise RuntimeError(mcp_tools._tool_error_payload(e)) from None


def build_mcp() -> Any:
    from mcp.server.fastmcp import FastMCP

    mcp = FastMCP(
        "kimss",
        instructions=(
            "Kimss API tools: chat, create/run agents, model completions, "
            "file upload, vector stores, function tools. Requires KIMSS_API_KEY."
        ),
    )

    @mcp.tool()
    def kimss_chat(
        assistant_id: str,
        message: str,
        conversation_id: str | None = None,
    ) -> Any:
        """Send a user message (POST /assistant_chat/). Returns API ``res`` payload."""
        return _run_tool(
            mcp_tools.kimss_chat,
            assistant_id=assistant_id,
            message=message,
            conversation_id=conversation_id,
        )

    @mcp.tool()
    def kimss_create_agent(
        name: str,
        model: str | None = None,
        instructions: str | None = None,
        metadata: dict[str, Any] | None = None,
        owner_id: str | None = None,
        tools: list[dict[str, Any]] | None = None,
        tenant_id: str | None = None,
    ) -> Any:
        """Create a Kimss agent (POST /v1/agents/create). Returns ``res`` (e.g. assistant_id)."""
        return _run_tool(
            mcp_tools.kimss_create_agent,
            name=name,
            model=model,
            instructions=instructions,
            metadata=metadata,
            owner_id=owner_id,
            tools=tools,
            tenant_id=tenant_id,
        )

    @mcp.tool()
    def kimss_run_agent(
        assistant_id: str,
        message: str,
        conversation_id: str | None = None,
        chat_type: str = "user_chat",
    ) -> Any:
        """Run an agent turn (POST /v1/agents/run), non-streaming only."""
        return _run_tool(
            mcp_tools.kimss_run_agent,
            assistant_id=assistant_id,
            message=message,
            conversation_id=conversation_id,
            chat_type=chat_type,
        )

    @mcp.tool()
    def kimss_complete(
        model: str,
        messages: list[dict[str, str]],
        system: str | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> Any:
        """Model completion without agent (POST /v1/models/completions), non-streaming."""
        return _run_tool(
            mcp_tools.kimss_complete,
            model=model,
            messages=messages,
            system=system,
            max_tokens=max_tokens,
            temperature=temperature,
        )

    @mcp.tool()
    def kimss_upload_file(
        path: str,
        filename: str | None = None,
        content_type: str = "application/octet-stream",
    ) -> Any:
        """Upload a local file (POST /v1/files/upload)."""
        return _run_tool(
            mcp_tools.kimss_upload_file,
            path=path,
            filename=filename,
            content_type=content_type,
        )

    @mcp.tool()
    def kimss_create_vector_store(
        name: str | None = None,
        agent_id: str | None = None,
        metadata: dict[str, Any] | None = None,
        tenant_id: str | None = None,
    ) -> Any:
        """Create a vector store (POST /v1/vector_stores/create)."""
        return _run_tool(
            mcp_tools.kimss_create_vector_store,
            name=name,
            agent_id=agent_id,
            metadata=metadata,
            tenant_id=tenant_id,
        )

    @mcp.tool()
    def kimss_add_function_to_agent(
        agent_id: str,
        name: str,
        description: str | None = None,
        parameters: dict[str, Any] | None = None,
    ) -> Any:
        """Add a function tool to an agent (POST /agent_add_function/)."""
        return _run_tool(
            mcp_tools.kimss_add_function_to_agent,
            agent_id=agent_id,
            name=name,
            description=description,
            parameters=parameters,
        )

    return mcp


def main() -> None:
    global _client
    api_key = (os.environ.get("KIMSS_API_KEY") or "").strip()
    if not api_key:
        sys.stderr.write(
            "kimss-mcp-server: Set KIMSS_API_KEY to a Kimss API key "
            "(Kimss app → Developer Settings → API Keys). Do not pass keys on the command line.\n"
        )
        raise SystemExit(1)
    base = (os.environ.get("KIMSS_BASE_URL") or "https://api.kimss.ai").rstrip("/")
    ws = (os.environ.get("KIMSS_WORKSPACE_ID") or "").strip() or None
    _client = KimssClient(api_key=api_key, base_url=base, workspace_id=ws)
    mcp = build_mcp()
    asyncio.run(mcp.run_stdio_async())


if __name__ == "__main__":
    main()
