# Kimss Python SDK — LLM / IDE context

Pair with [AI_INTEGRATION.md](../AI_INTEGRATION.md), [README.md](../README.md), and [KIMSS_ONBOARDING.md](KIMSS_ONBOARDING.md).

## Clean machine checklist (do this first)

1. **Python ≥ 3.10** available.
2. For **inference**: `pip install openai` — point at Kimss gateway (no Kimss SDK required).
3. Optional control-plane package: `pip install kimss` (register agents, report usage). Declared dep: `requests>=2.28`.
4. Set env: `KIMSS_WORKSPACE_KEY` or `KIMSS_API_KEY`, `KIMSS_AGENT_ID`, optional `KIMSS_GATEWAY_URL` (default `https://api.kimss.ai/v1`).
5. **Preferred first call:** official OpenAI client → `POST /v1/chat/completions` with `X-Kimss-Agent-Id`.
6. **Deprecated:** `KimssClient.agents.run`, `chat`, `Agent.query`, `models.create`, MCP `kimss_chat` / `kimss_run_agent` / `kimss_complete`.

## Preferred inference (gateway proxy)

```python
import os
from openai import OpenAI

client = OpenAI(
    base_url=os.getenv("KIMSS_GATEWAY_URL", "https://api.kimss.ai/v1"),
    api_key=os.getenv("KIMSS_WORKSPACE_KEY") or os.getenv("KIMSS_API_KEY"),
)
resp = client.chat.completions.create(
    model=os.getenv("KIMSS_MODEL", "custom:your-vaulted-model"),
    messages=[{"role": "user", "content": "Hello"}],
    extra_headers={
        "X-Kimss-Agent-Id": os.getenv("KIMSS_AGENT_ID", "my_agent"),
        "X-Kimss-Agent-Name": os.getenv("KIMSS_AGENT_NAME", "My Agent"),
    },
)
```

Auth on `/v1`: `Authorization: Bearer kimss_...` or `X-Kimss-Key`.

## Control plane (DevOps) — `kimss` package

| Concern | How |
|---------|-----|
| Register external agent | `client.agents.register(...)` → `POST /v1/agents/register` |
| Report BYO usage | `client.usage.report(...)` → `POST /v1/usage/events` |
| Kill switch | Governance UI or `POST /agent_set_status/` `{id, status: "disabled"\|"active"}` (admin) |
| Article 12–style audit | Gateway → Recent calls; `POST /audit_log/` for tenant admin events; APIM GatewayLogs when enabled |
| MCP sync | Control Plane / Connected Infrastructure (UI); do not invent a public MCP HTTP proxy URL |

Native auth for control-plane calls: **`X-Kimss-Key`**. Base URL for `KimssClient`: `https://api.kimss.ai` (no `/v1` suffix).

## Deprecated SDK method → HTTP map

| SDK surface (deprecated for inference) | HTTP |
|----------------------------------------|------|
| `KimssClient.chat` / `Agent.query` / `agents.run` | `POST /v1/agents/run` |
| `KimssClient.models.create` | `POST /v1/models/completions` |
| `KimssClient.images.generate` | `POST /v1/images/generations` |

Still valid management: `agents.create`, `agents.register`, `usage.report`, `files.upload`, `add_function_to_agent`.

## OpenAI-compatible base URL

```text
base_url = https://api.kimss.ai/v1
api_key  = kimss_...
headers  = X-Kimss-Agent-Id, X-Kimss-Agent-Name
```

Do **not** point Anthropic Messages or Azure official clients at Kimss inbound URLs.

## Error code dictionary

| HTTP | `detail.error` | Meaning |
|------|----------------|---------|
| 403 | `agent_disabled` | Kill switch — stop; re-enable in Governance |
| 403 | `subscription_required` | Upgrade / switch workspace |
| 429 | `governed_requests_exhausted` | Monthly free allowance hit |
| 429 | `credit_pool_exhausted` / trial / policy | Stop; surface to user |
| 429 | `rate_limit_exceeded` | Backoff / Retry-After |

## MCP tools (stdio) — optional IDE

Install: `pip install 'kimss[mcp]'`. Inference tools (`kimss_chat`, `kimss_run_agent`, `kimss_complete`) are **deprecated**; prefer OpenAI gateway from app code. Management tools remain for create/upload/function attach.
