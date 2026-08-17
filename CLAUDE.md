# Kimss Python SDK — Claude Code

Read [docs/KIMSS_ONBOARDING.md](docs/KIMSS_ONBOARDING.md) before changing customer LLM clients.

1. OpenAI clients → `base_url=https://api.kimss.ai/v1`, key `kimss_...` / `KIMSS_API_KEY`.
2. Native `KimssClient` → `base_url=https://api.kimss.ai` (no `/v1`), header `X-Kimss-Key`.
3. Do not rewrite Anthropic or Azure official SDKs to Kimss inbound URLs.
4. Do not change model/tool payloads unless asked.
5. Kill switch: HTTP 403 `agent_disabled`. Never say “zero-trust”.

Dense map: [docs/llm-context.md](docs/llm-context.md). Humans: [GETTING_STARTED.md](GETTING_STARTED.md).
