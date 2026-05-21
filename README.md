# Kimss Python SDK

Lightweight client for the [Kimss](https://kimss.ai) API. Use it to call your Kimss agents from Python scripts, backends, or notebooks.

## Install

```bash
pip install kimss
```

Optional **PII redaction** (Microsoft Presidio + spaCy model, e.g. `python -m spacy download en_core_web_lg`):

```bash
pip install 'kimss[privacy]'
```

Or from this repo (editable):

```bash
cd kimss_sdk && pip install -e .
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

## API

- **`KimssClient(..., retry=None)`** – authenticated client. Provide either `api_key` (uses `X-Kimss-Key`) or `credential` + `token_scope` (uses `Authorization: Bearer`). `workspace_id` optionally stamps `X-Workspace-ID` and `tenant_id` for isolated worker telemetry. Uses a `requests.Session` with **retry on 5xx** (not 429) and **Retry-After** by default so credit exhaustion and rate limits surface immediately as typed errors (`KimssCreditExhausted`, `KimssRateLimited`, `KimssSubscriptionRequired`).
- **`client.get_agent(agent_id)`** – returns an `Agent` for that assistant.
- **`agent.query(message, thread_id=None, chat_type="user_chat")`** – send a message; returns the `res` object from `POST /assistant_chat/`.
- **`client.chat(assistant_id, message, thread_id=None, chat_type="user_chat")`** – one-off chat without an Agent handle.
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
`Authorization: Bearer <token>`. No streaming in this version; responses are full JSON.

## Usage Hub (execution context)

For agent and model calls, the SDK automatically adds an optional **`X-Kimss-SDK-Context`** header (base64url JSON) with:

- **`host_environment`** — e.g. Azure `WEBSITE_SITE_NAME`, `GitHub:org/repo`, or `Local/Dev`
- **`source_location`** — best-effort path to the caller's Python file (relative to `getcwd()` when possible)
- **`resource_type`** / **`resource_name`** — `agent` or `model` plus assistant id or model id

Paths are resolved in your process and sent as metadata for the workspace **Usage** dashboard. Use `before_request_hooks` to remove that header from `ctx["headers"]` if your policy forbids file paths.
