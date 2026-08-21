# KIMSS GATEWAY AGENT INSTRUCTIONS

Dual-listener Secure AI Gateway. Never “zero-trust”.

1. Keep the developer's native `openai` or `anthropic` SDK.
2. OpenAI → `base_url=https://api.kimss.ai/v1`. Anthropic → `base_url=https://api.kimss.ai`.
3. Always inject `X-Kimss-Agent-Id` / `X-Kimss-Agent-Name`.
4. Never use `KimssClient` for chat/completions/messages.
5. Kill switch: `agent_disabled`. Keys: `kimss_...`.

See [AI_INTEGRATION.md](../AI_INTEGRATION.md).
