# AI Integration — Kimss Gateway (Agent-to-Agent)

**Strict directive for Cursor, Windsurf, Claude Code, Devin, and other coding assistants.**

Kimss is a **Model-Agnostic Enterprise AI Gateway and Governance Control Plane** with a **dual-listener** inbound proxy:

- OpenAI syntax → `POST https://api.kimss.ai/v1/chat/completions`
- Anthropic syntax → `POST https://api.kimss.ai/v1/messages`

## Rules (do not violate)

1. **Never** use a custom `KimssClient` for chat/completions/messages or any LLM inference.
2. **Identify** whether the user's codebase uses the `openai` or `anthropic` SDK natively. **Keep their native SDK** — zero data-plane refactoring.
3. **For OpenAI:** set `base_url` to `https://api.kimss.ai/v1`.
4. **For Anthropic:** set `base_url` to `https://api.kimss.ai` (the SDK appends `/v1/messages`).
5. **Always** inject `X-Kimss-Agent-Id` (and preferably `X-Kimss-Agent-Name`) for JIT attribution, audit, and kill-switch.
6. Hermis / HTTP interceptors: forward Agent-Id headers; never strip them.

## OpenAI

```python
from openai import OpenAI

client = OpenAI(
    base_url="https://api.kimss.ai/v1",
    api_key="kimss_workspace_key",
)
response = client.chat.completions.create(
    model="custom:kimss-gpt-5-3",
    messages=[{"role": "user", "content": "Execute audit."}],
    extra_headers={"X-Kimss-Agent-Id": "enterprise_auditor"},
)
```

## Anthropic

```python
from anthropic import Anthropic

client = Anthropic(
    base_url="https://api.kimss.ai",
    api_key="kimss_workspace_key",
)
response = client.messages.create(
    model="custom:kimss-claude-3-5",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Execute audit."}],
    extra_headers={"X-Kimss-Agent-Id": "enterprise_auditor"},
)
```

Auth also accepts `X-Kimss-Key` and Anthropic-style `x-api-key` with a `kimss_...` workspace key.

## What `KimssClient` is for

Control-plane / DevOps only (`agents.register`, `usage.report`). Inference methods are deprecated.

## Kill switch

HTTP **403** with `agent_disabled` (OpenAI `error.code` or Anthropic error body). Never say “zero-trust”.
