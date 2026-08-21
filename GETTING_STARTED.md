# Getting started with the Kimss Secure AI Gateway

**Track, govern, and secure autonomous agents with exactly 1 line of code.**

Kimss is the **Secure AI Gateway** and **Governance Control Plane**: identity, audit, kill switch, and a provider vault. You bring the models (**BYOI**).

**Developer tier (Always Free):** 25,000 governed requests/month. No credit card.

## Step 1 — Sign In & Vault

Open **Governance → Provider Vault** / Connected Infrastructure (`/app/governance/custom-models`). Add your OpenAI, Azure OpenAI / Foundry, Anthropic, DeepSeek, or vLLM endpoint. The key is vaulted and never returned to clients.

## Step 2 — Mint a Control-Plane key

Open **Gateway** → **Generate Key**. Copy the `kimss_...` secret once. Same keys under **Governance → API Keys**.

## Step 3 — Route traffic (zero refactoring)

### OpenAI client (recommended)

```python
import os
from openai import OpenAI

client = OpenAI(
    base_url=os.getenv("KIMSS_GATEWAY_URL", "https://api.kimss.ai/v1"),
    api_key=os.getenv("KIMSS_WORKSPACE_KEY") or os.getenv("KIMSS_API_KEY"),
)
response = client.chat.completions.create(
    model=os.getenv("KIMSS_MODEL", "custom:your-vaulted-model"),
    messages=[{"role": "user", "content": "Hello via Kimss Gateway"}],
    extra_headers={
        "X-Kimss-Agent-Id": os.getenv("KIMSS_AGENT_ID", "my_agent"),
        "X-Kimss-Agent-Name": os.getenv("KIMSS_AGENT_NAME", "My Agent"),
    },
)
```

### Zero-code `.env`

```bash
OPENAI_BASE_URL="https://api.kimss.ai/v1"
OPENAI_API_KEY="kimss_your_kimss_key"
```

Official Anthropic and Azure SDKs are **not** inbound drop-ins. Vault those providers, then call Kimss with the OpenAI-compatible `/v1` client.

## Step 4 — Monitor and kill switch

- **Gateway → Recent calls** — attributed to your `X-Kimss-Agent-Id` (or JIT-discovered).
- **Governance → Agents** — disable an agent → HTTP **403** `agent_disabled`.

## Control plane (optional)

`pip install kimss` for `agents.register` and `usage.report`. Kill switch / audit / MCP sync: Governance UI or REST (`POST /agent_set_status/`, `POST /audit_log/`). Do not use `KimssClient` for chat/completions.

## Related

- [AI_INTEGRATION.md](AI_INTEGRATION.md) — mandatory rules for AI coding assistants
- [README.md](README.md)
- [docs/llm-context.md](docs/llm-context.md)
