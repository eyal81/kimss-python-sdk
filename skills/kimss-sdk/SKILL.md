---
name: kimss-sdk
description: Integrate Kimss via OpenAI gateway proxy (base_url + Agent-Id headers). Optional kimss package for control-plane register/usage only.
---

# Kimss Python SDK / Gateway

## When to use

- Routing app traffic through Kimss (identity, audit, kill switch).
- Optional DevOps: register external agents, report BYO usage.

## Preferred inference (no Kimss SDK)

```bash
pip install openai
```

```python
import os
from openai import OpenAI

client = OpenAI(
    base_url=os.getenv("KIMSS_GATEWAY_URL", "https://api.kimss.ai/v1"),
    api_key=os.getenv("KIMSS_WORKSPACE_KEY") or os.getenv("KIMSS_API_KEY"),
)
resp = client.chat.completions.create(
    model=os.getenv("KIMSS_MODEL", "custom:your-model"),
    messages=[{"role": "user", "content": "Hello"}],
    extra_headers={
        "X-Kimss-Agent-Id": os.getenv("KIMSS_AGENT_ID", "my_agent"),
        "X-Kimss-Agent-Name": os.getenv("KIMSS_AGENT_NAME", "My Agent"),
    },
)
```

## Control plane (optional)

```bash
pip install kimss
```

```python
from kimss import KimssClient
client = KimssClient(api_key="kimss_...", base_url="https://api.kimss.ai")
client.agents.register(name="Database Auditor", agent_id="enterprise_db_auditor")
```

## Deprecated (do not generate new call sites)

`client.agents.run`, `client.chat`, `Agent.query`, `client.models.create`, MCP `kimss_chat` / `kimss_run_agent` / `kimss_complete`.

## Errors

Kill switch: `agent_disabled`. Also: `KimssCreditExhausted`, `KimssRateLimited`, `KimssSubscriptionRequired`, `KimssGovernedRequestsExhausted`.

## Reference

- [AI_INTEGRATION.md](../../AI_INTEGRATION.md)
- [docs/llm-context.md](../../docs/llm-context.md)
- [examples/00_gateway_proxy.py](../../examples/00_gateway_proxy.py)
