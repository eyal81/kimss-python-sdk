---
name: kimss-sdk
description: Build and debug integrations with the Kimss Python SDK — clients, agents.run, models, ephemeral file upload, function tools, streaming, and errors.
---

# Kimss Python SDK

## When to use

- Writing or reviewing Python that calls Kimss (agents, models, ephemeral file upload).
- Choosing between `agents.run`, `chat` / `Agent.query`, and MCP tools.
- Handling credits, rate limits, subscriptions, and conversation threading.

## Install

```bash
pip install kimss
# optional: pip install 'kimss[mcp]' 'kimss[privacy]' 'kimss[dev]'
```

## Client setup

```python
from kimss import KimssClient

client = KimssClient(
    api_key="kimss_...",  # from Kimss app → Developer Settings → API Keys
    base_url="https://api.kimss.ai",  # no trailing slash; staging: https://stg.kimss.ai
    workspace_id="my-workspace-slug",  # optional → X-Workspace-ID / tenant_id
)
```

Headless Entra: `KimssClient(credential=..., token_scope="api://<app-id>/.default", base_url=..., workspace_id=...)`.

## Agent runs (preferred)

```python
result = client.agents.run("asst_xxxx", "Hello", stream=False)
# AgentRunResult: .text, .usage.total_credits, .conversation_id
follow = client.agents.run(
    "asst_xxxx",
    "Follow-up",
    stream=False,
    conversation_id=result.conversation_id,
)
```

Aliases: `agent_id` / `prompt`. JSON wire uses `thread_id` for the conversation id.

## Legacy chat

`client.chat(...)` or `client.get_agent(id).query(...)` → `POST /v1/agents/run`. Same `conversation_id` / `thread_id` pattern.

## Models

`client.models.create(model=..., messages=[...], stream=False)` → `POST /v1/models/completions`.

## Files

- `client.files.upload(path, ...)` → multipart `POST /v1/files/upload` (ephemeral attachments; Kimss does not host RAG).

## Function tools (owned agents only)

`client.add_function_to_agent(assistant_id, name, description, parameters)` or `Agent.add_function(...)` → `POST /agent_add_function/`. JSON Schema object for `parameters`. Shared agents cannot be modified — expect 403.

## Streaming

`stream=True` on `agents.run` / `models.create` yields SSE JSON chunks. **MCP v1 tools are non-streaming only.**

## Errors

Typed exceptions: `KimssCreditExhausted`, `KimssRateLimited`, `KimssSubscriptionRequired`, `KimssApiError`. Do not blind-retry 429 credit or subscription errors.

## Reference

- [docs/llm-context.md](../../docs/llm-context.md) — endpoint map and error table.
- [README.md](../../README.md) — MCP, Usage Hub header, examples path `examples/`.
