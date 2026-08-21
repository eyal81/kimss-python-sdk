# Kimss — Secure AI Gateway for Autonomous Agents

[![PyPI](https://img.shields.io/pypi/v/kimss.svg?color=indigo)](https://pypi.org/project/kimss/)
[![Python](https://img.shields.io/pypi/pyversions/kimss.svg?color=purple)](https://pypi.org/project/kimss/)
[![License: MIT](https://img.shields.io/badge/License-MIT-indigo.svg)](LICENSE)
[![CI](https://img.shields.io/badge/CI-indigo?logo=github)](https://github.com/eyal81/kimss-python-sdk/actions/workflows/ci.yml)

**Track, govern, and secure autonomous agents with exactly 1 line of code.**

[Kimss](https://kimss.ai) is a **Model-Agnostic Enterprise AI Gateway** and **Governance Control Plane**. Swap your OpenAI `base_url`, add an Agent ID header, and every call gets identity, an audit trail, and a kill switch — without rewriting your app. Kimss never hosts your models and never charges for inference compute (**BYOI**).

> **AI coding assistants:** read [AI_INTEGRATION.md](AI_INTEGRATION.md) first.

```python
import os
from openai import OpenAI

client = OpenAI(
    base_url=os.getenv("KIMSS_GATEWAY_URL", "https://api.kimss.ai/v1"),
    api_key=os.getenv("KIMSS_WORKSPACE_KEY") or os.getenv("KIMSS_API_KEY"),
)

response = client.chat.completions.create(
    model="custom:kimss-gpt-5-3-chat",
    messages=[{"role": "user", "content": "Execute database audit."}],
    extra_headers={
        "X-Kimss-Agent-Id": "enterprise_db_auditor",
        "X-Kimss-Agent-Name": "Database Auditor Agent",
    },
)
```

Or zero-code:

```bash
OPENAI_BASE_URL="https://api.kimss.ai/v1"
OPENAI_API_KEY="kimss_..."
```

**Developer tier (Always Free):** 25,000 governed requests/month · [Get a key](https://kimss.ai/app/signup)

| Inbound (your app → Kimss) | Vaulted BYO (Kimss → your provider) |
|----------------------------|-------------------------------------|
| OpenAI Python/JS/Java at `https://api.kimss.ai/v1` | OpenAI, Azure AI Foundry, Anthropic, DeepSeek, custom vLLM |
| Agent attribution via `X-Kimss-Agent-Id` | Internal MCP servers (Control Plane registration) |

```mermaid
flowchart LR
  App[Your_app_or_agent] --> GW["Kimss_Gateway"]
  GW --> Model[Vaulted_provider]
  GW --> Trail[Governed_audit_trail]
```

---

## 3-step setup

### 1. Sign In & Vault

Log into [Kimss AI](https://kimss.ai/app/signup). Open **Governance → Connected Infrastructure** / Provider Vault and vault your model provider endpoint + key.

### 2. Mint Key

On the **Gateway** tab, **Generate Key**. Copy the `kimss_...` Control-Plane workspace key once. Same keys under **Governance → API Keys**.

### 3. Route Traffic (zero refactoring)

Point your OpenAI client at `https://api.kimss.ai/v1`, set the key, and add `X-Kimss-Agent-Id` (see hero snippet). Prefer a registered `agent_id` from **Gateway**; omit it and Kimss may JIT-discover the agent from traffic.

Step-by-step: [GETTING_STARTED.md](GETTING_STARTED.md) · 5-minute tutorial: [eyal81/kimss-python-quickstart](https://github.com/eyal81/kimss-python-quickstart).

---

## Control plane (DevOps) — optional `pip install kimss`

The **`kimss`** package is an **infrastructure management** client — not an inference SDK. Prefer the OpenAI gateway for all chat/completions.

| Concern | How |
|---------|-----|
| Register external agent | `client.agents.register(...)` → `POST /v1/agents/register` |
| Report BYO usage | `client.usage.report(...)` → `POST /v1/usage/events` |
| Kill switch | Governance → Agents, or `POST /agent_set_status/` `{ "id", "status": "disabled" }` (admin) |
| Article 12–style audit | Gateway → Recent calls; `POST /audit_log/`; APIM GatewayLogs when enabled |
| MCP sync | Control Plane / Connected Infrastructure (UI registration) |

```bash
pip install kimss
```

Inference wrappers (`agents.run`, `chat`, `models.create`, …) are **deprecated** — see [CHANGELOG.md](CHANGELOG.md).

---

## Optional: MCP for IDEs

Cursor / Windsurf / Claude Desktop can run `kimss-mcp-server` (`pip install 'kimss[mcp]'` or `uvx --from kimss[mcp] kimss-mcp-server`). MCP inference tools are deprecated; use the OpenAI gateway from application code. Plugin layout: [`.cursor-plugin/plugin.json`](.cursor-plugin/plugin.json).

---

## Examples

See [examples/00_gateway_proxy.py](examples/00_gateway_proxy.py) for the canonical pattern.

## License

MIT — see [LICENSE](LICENSE).
