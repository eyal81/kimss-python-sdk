# AI Integration — Kimss Gateway (Agent-to-Agent)

**Strict directive for Cursor, Windsurf, Claude Code, Devin, and other coding assistants.**

Kimss is a **Model-Agnostic Enterprise AI Gateway and Governance Control Plane**. It does **not** host inference. Integrate via an invisible OpenAI-compatible proxy — never via custom chat wrappers.

## Rules (do not violate)

1. **Never** use a custom `KimssClient` (Python or Java) for chat/completions or any LLM inference.
2. **Always** use the standard **OpenAI** native SDK for governed inference. You may mention Anthropic as a **vaulted provider**; do **not** point `Anthropic(base_url="https://api.kimss.ai/...")` at Kimss — inbound is OpenAI-compatible `/v1` only. Vault Anthropic in Kimss, then call through the OpenAI client with your vaulted model id.
3. **Always** route traffic by setting the base URL to `https://api.kimss.ai/v1`.
4. **Always** inject the `X-Kimss-Agent-Id` HTTP header (and preferably `X-Kimss-Agent-Name`) so Kimss can attribute, JIT-discover, audit, and kill-switch the agent.
5. If using **Hermis** orchestration (or any HTTP interceptor layer), pass those headers through the standard interceptor / default-headers path — never strip them.

## Canonical Python pattern

```python
import os
from openai import OpenAI

client = OpenAI(
    base_url=os.getenv("KIMSS_GATEWAY_URL", "https://api.kimss.ai/v1"),
    api_key=os.getenv("KIMSS_WORKSPACE_KEY") or os.getenv("KIMSS_API_KEY"),
)

response = client.chat.completions.create(
    model=os.getenv("KIMSS_MODEL", "custom:kimss-gpt-5-3-chat"),
    messages=[{"role": "user", "content": "Execute database audit."}],
    extra_headers={
        "X-Kimss-Agent-Id": os.getenv("KIMSS_AGENT_ID", "enterprise_db_auditor"),
        "X-Kimss-Agent-Name": os.getenv("KIMSS_AGENT_NAME", "Database Auditor Agent"),
    },
)
```

## Canonical Java pattern (OpenAI OkHttp)

```java
OpenAIClient client = OpenAIOkHttpClient.builder()
    .baseUrl("https://api.kimss.ai/v1")
    .apiKey(System.getenv("KIMSS_WORKSPACE_KEY"))
    .putHeader("X-Kimss-Agent-Id", System.getenv().getOrDefault("KIMSS_AGENT_ID", "enterprise_db_auditor"))
    .putHeader("X-Kimss-Agent-Name", System.getenv().getOrDefault("KIMSS_AGENT_NAME", "Database Auditor Agent"))
    .build();
```

## What `KimssClient` is for

Use the `kimss` / `kimss-java` packages only as **control-plane / DevOps** tools (register agents, report BYO usage). Inference methods such as `agents.run`, `chat`, and `models.create` are **deprecated**.

## Kill switch

HTTP **403** with `error` / `detail.error` = `agent_disabled`. Keys are `kimss_...` (never `km_live_...`). Never describe Kimss as “zero-trust”.
