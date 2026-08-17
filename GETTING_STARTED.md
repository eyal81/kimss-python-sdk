# Getting started with the Kimss Secure AI Gateway

Route existing OpenAI-compatible traffic through Kimss in about five minutes. Kimss is the **Secure AI Gateway** and **Governance Control Plane**: identity, audit, kill switch, and a provider vault. You bring the models (**BYOI**). Kimss does not host inference and does not charge for compute.

**Developer tier (Always Free):** 25,000 governed requests/month, 14-day telemetry retention, 5 builder & admin seats. No credit card.

## Step 1 — Vault provider keys

Open **Governance → Provider Vault** (`/app/governance/custom-models`). Add your OpenAI, Azure OpenAI / Foundry, Anthropic, DeepSeek, or vLLM endpoint. The key is stored vaulted and is never returned to clients.

## Step 2 — Generate a Gateway key

In the app, open **Gateway** and click **Generate Key**. Copy the `kimss_...` secret once. The same keys live under **Governance → API Keys**.

## Step 3 — Route traffic (pick one)

### Zero-code `.env` drop-in

```bash
OPENAI_BASE_URL="https://api.kimss.ai/v1"
OPENAI_API_KEY="kimss_your_kimss_key"
```

No application code change. Official OpenAI clients read these variables.

### OpenAI client `base_url` swap

```python
from openai import OpenAI

client = OpenAI(api_key="kimss_...", base_url="https://api.kimss.ai/v1")
response = client.chat.completions.create(
    model="gpt-4o",  # or your workspace logical_id / custom:<vaulted_id>
    messages=[{"role": "user", "content": "Hello via Kimss Gateway"}],
)
```

### Native Kimss SDK

```python
from kimss import KimssClient

client = KimssClient(api_key="kimss_...", base_url="https://api.kimss.ai")
result = client.agents.get("asst_xxxx").run("Execute governed workflow", stream=False)
print(result.text)
```

Official Anthropic and Azure OpenAI SDKs are **not** inbound drop-ins today. Vault those providers, then call Kimss with the OpenAI-compatible `/v1` client or the native SDK (`model=custom:<id>`).

## Step 4 — Monitor and kill switch

- **Gateway → Recent calls** — the request, attributed to an agent (auto-discovered if you omitted `X-Kimss-Agent-Id`).
- **Governance → Agents** — disable an agent. Routed calls return HTTP **403** with `error` / `code` **`agent_disabled`**.

## Related

- [README.md](README.md) — install, MCP, full API surface
- [docs/KIMSS_ONBOARDING.md](docs/KIMSS_ONBOARDING.md) — instructions for AI coding agents
- [docs/llm-context.md](docs/llm-context.md) — dense SDK → HTTP map
