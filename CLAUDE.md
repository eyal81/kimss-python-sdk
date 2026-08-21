# Kimss Python SDK — Claude Code

Read [AI_INTEGRATION.md](AI_INTEGRATION.md) before changing customer LLM clients.

1. Never use `KimssClient` for chat/completions.
2. OpenAI clients → `base_url=https://api.kimss.ai/v1`, key `kimss_...` / `KIMSS_WORKSPACE_KEY` / `KIMSS_API_KEY`.
3. Always send `X-Kimss-Agent-Id` (and preferably `X-Kimss-Agent-Name`).
4. Do not rewrite Anthropic or Azure official SDKs to Kimss inbound URLs — vault those providers and call via OpenAI-compat `/v1`.
5. Hermis: pass Agent-Id headers through the HTTP interceptor layer.
6. Kill switch: HTTP 403 `agent_disabled`. Never say “zero-trust”.

Dense map: [docs/llm-context.md](docs/llm-context.md). Humans: [GETTING_STARTED.md](GETTING_STARTED.md).
