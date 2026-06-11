---
name: kimss-diagnose
description: Triage Kimss connectivity, identity, and common API errors (whoami, agent list, credits, rate limits).
---

# Kimss — diagnose integration issues

1. **MCP process:** If tools never appear, verify `uvx`/`kimss-mcp-server` and `KIMSS_API_KEY` in MCP env; restart the MCP client.
2. **Identity (HTTP):** With the same API key, `GET https://api.kimss.ai/whoami` (or staging host) should return JSON describing account/plan context — use this to confirm the key is valid and environment matches `KIMSS_BASE_URL`. Do not paste full responses into logs if they contain PII.
3. **Agent listing:** SDK `client.chat`-style listing is via legacy assistant list endpoints in product; for quick validation prefer a known `assistant_id` from the user or a successful `kimss_run_agent` / `kimss_chat` call.
4. **429 credit / subscription:** Map to `KimssCreditExhausted` / `KimssSubscriptionRequired` in SDK; advise workspace billing or wait — no tight retry loops.
5. **429 rate limit:** Honor `Retry-After`; backoff and retry.
6. **404 feature_disabled:** Gateway feature may be off for that workspace — not fixable client-side by changing host away from canonical `api.kimss.ai` / `stg.kimss.ai`.
7. **403 on mutate:** Agent may be shared or key lacks scope — align with owned agents and management keys for create/update/function tools.

Reference: [docs/llm-context.md](../docs/llm-context.md).
