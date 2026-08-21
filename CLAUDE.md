# Kimss Python SDK — Claude Code

Read [AI_INTEGRATION.md](AI_INTEGRATION.md).

Dual-listener: OpenAI `/v1/chat/completions` and Anthropic `/v1/messages`. Keep the native SDK already in the repo. Never use `KimssClient` for inference. Always send `X-Kimss-Agent-Id`.
