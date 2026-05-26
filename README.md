# Kimss Python SDK & MCP server

[![PyPI](https://img.shields.io/pypi/v/kimss.svg)](https://pypi.org/project/kimss/)
[![Python](https://img.shields.io/pypi/pyversions/kimss.svg)](https://pypi.org/project/kimss/)

Lightweight client for the [Kimss](https://kimss.ai) API — call agents, run model completions, upload files, and manage vector stores from Python. Optional **Model Context Protocol (MCP)** server for **Cursor**, **Windsurf**, and other MCP-capable IDEs.

**AI assistants:** read [docs/llm-context.md](docs/llm-context.md) or the repo root [.llms.txt](.llms.txt) for dense integration context.

## Cursor & Windsurf (MCP) — zero local venv with `uvx`

Install the MCP extra on the fly and expose tools to your IDE:

```json
{
  "mcpServers": {
    "kimss": {
      "command": "uvx",
      "args": ["--with", "kimss[mcp]", "kimss-mcp-server"],
      "env": {
        "KIMSS_API_KEY": "your_key_here",
        "KIMSS_BASE_URL": "https://api.kimss.ai",
        "KIMSS_WORKSPACE_ID": ""
      }
    }
  }
}
```

- Set `KIMSS_API_KEY` to a long-lived key from **Developer Settings → API Keys** (never commit it).
- Optional `KIMSS_WORKSPACE_ID` stamps `X-Workspace-ID` / `tenant_id` for workspace-scoped calls.
- MCP tools are **non-streaming** in v1 (`kimss_chat`, `kimss_create_agent`, `kimss_run_agent`, `kimss_complete`, `kimss_upload_file`, `kimss_create_vector_store`, `kimss_add_function_to_agent`).

Alternatively, after `pip install 'kimss[mcp]'`, use `"command": "kimss-mcp-server"` on your PATH with the same `env`.

## Install (library)

```bash
pip install kimss
```

Optional **PII redaction** (Microsoft Presidio + spaCy; e.g. `python -m spacy download en_core_web_lg`):

```bash
pip install 'kimss[privacy]'
```

Other extras:

```bash
pip install 'kimss[mcp]'   # MCP server (stdio)
pip install 'kimss[types]' # Pydantic (reserved for future typed models)
pip install 'kimss[dev]'    # pytest, responses, ruff
```

Editable from a checkout of this package root:

```bash
cd kimss_sdk && pip install -e ".[dev,mcp]"
```

## Authentication

Use a **long-lived API key** (not a browser session token). Create keys in your Kimss app under **Developer Settings → API Keys**. The key is scoped to your tenant and user.

Headless workers can also authenticate with Microsoft Entra ID by passing
an Azure credential plus a Kimss API token scope:

```python
from azure.identity import DefaultAzureCredential
from kimss import KimssClient

client = KimssClient(
    base_url="https://api.kimss.ai",
    credential=DefaultAzureCredential(),
    token_scope="api://<kimss-api-app-id>/.default",
    workspace_id="worksfusion",
)
```

## Usage

Use the canonical Kimss API host. Production is `https://api.kimss.ai` and staging is `https://stg.kimss.ai`; do not include a trailing slash.

```python
from kimss import KimssClient, Agent

client = KimssClient(
    api_key="kimss_xxxxxxxxxxxxxxxxxxxxxxxx",  # from Developer Settings
    base_url="https://api.kimss.ai",  # no trailing slash
)

# Get an agent and send a message
agent = client.get_agent(agent_id="asst_xxxx")
result = agent.query("Hello")
# result is the API "res" payload (run_id, thread_id, messages, usage, etc.)

# Continue a thread
result2 = agent.query("What did I just say?", thread_id=result.get("thread_id"))

# Or use the client directly
result3 = client.chat(assistant_id="asst_xxxx", message="Hi", thread_id=result.get("thread_id"))
```

### Streaming

`client.models.create(..., stream=True)` and `client.agents.run(..., stream=True)` return an **SSE iterator** of JSON objects. The MCP server does not expose streaming tools in v1.

## API

- **`KimssClient(..., retry=None)`** – authenticated client. Provide either `api_key` (uses `X-Kimss-Key`) or `credential` + `token_scope` (uses `Authorization: Bearer`). `workspace_id` optionally stamps `X-Workspace-ID` and `tenant_id` for isolated worker telemetry. Uses a `requests.Session` with **retry on 5xx** (not 429) and **Retry-After** by default so credit exhaustion and rate limits surface immediately as typed errors (`KimssCreditExhausted`, `KimssRateLimited`, `KimssSubscriptionRequired`).
- **`client.get_agent(agent_id)`** – returns an `Agent` for that assistant.
- **`agent.query(message, thread_id=None, chat_type="user_chat")`** – send a message; returns the `res` object from `POST /assistant_chat/`.
- **`client.chat(assistant_id, message, thread_id=None, chat_type="user_chat")`** – one-off chat without an Agent handle.
- **`client.agents.create` / `client.agents.run`** – v1 agent management and orchestration (`/v1/agents/create`, `/v1/agents/run`).
- **`client.models.create`** – `/v1/models/completions`.
- **`client.files.upload`** – `/v1/files/upload`.
- **`client.vector_stores.create`** – `/v1/vector_stores/create`.
- **`before_request_hooks`** – list of callables `hook(ctx)` where `ctx` is `{"path": str, "json": dict, "headers": dict}`; hooks may mutate `json` / `headers` before the HTTP POST.
- **`privacy`** – shortcut for `PresidioRedactor()` from `kimss.privacy` (requires `kimss[privacy]`).

```python
from kimss import KimssClient, PresidioRedactor

client = KimssClient(
    api_key="kimss_...",
    base_url="https://api.kimss.ai",
    privacy=PresidioRedactor(),
)
```

API-key requests use the `X-Kimss-Key` header. Credential requests use
`Authorization: Bearer <token>`. Non-streaming responses are full JSON dicts from the API `res` envelope where applicable.

## Examples

See [examples/](examples/) — set `KIMSS_API_KEY` (and `KIMSS_ASSISTANT_ID` / `KIMSS_MODEL` where noted).

## Usage Hub (execution context)

For agent and model calls, the SDK automatically adds an optional **`X-Kimss-SDK-Context`** header (base64url JSON) with:

- **`host_environment`** — e.g. Azure `WEBSITE_SITE_NAME`, `GitHub:org/repo`, or `Local/Dev`
- **`source_location`** — best-effort path to the caller's Python file (relative to `getcwd()` when possible)
- **`resource_type`** / **`resource_name`** — `agent` or `model` plus assistant id or model id

Paths are resolved in your process and sent as metadata for the workspace **Usage** dashboard. Use `before_request_hooks` to remove that header from `ctx["headers"]` if your policy forbids file paths.

## Contributing & release

See [CONTRIBUTING.md](CONTRIBUTING.md) for tests, mirror workflow, and PyPI trusted publishing. **Operator bookmark (monorepo):** [3-step release routine](../plans/2026-05-26-kimss-sdk-release-routine.md).
