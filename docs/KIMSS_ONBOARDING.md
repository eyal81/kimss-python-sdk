# KIMSS GATEWAY AGENT INSTRUCTIONS

Kimss is a **Secure AI Gateway** and **Governance Control Plane**. Do not describe it as “zero-trust”.

When asked to integrate Kimss into an existing codebase:

1. Locate where OpenAI (or OpenAI-compat) clients are initialized.
2. Set `base_url` to `https://api.kimss.ai/v1`.
3. Set the API key to the Kimss workspace Control-Plane key (`kimss_...` / `KIMSS_WORKSPACE_KEY` / `KIMSS_API_KEY` / `OPENAI_API_KEY`).
4. **Always** inject `X-Kimss-Agent-Id` and preferably `X-Kimss-Agent-Name` (OpenAI Python: `extra_headers=...`).
5. Do **not** modify model payloads, tool schemas, or completion parameters unless specifically requested.
6. **Never** use `KimssClient` for chat/completions. Inference wrappers (`agents.run`, `chat`, `models.create`) are deprecated.
7. Do **not** rewrite Anthropic `Anthropic(base_url="https://api.kimss.ai/...")` or Azure inbound URLs. Vault Anthropic / Azure in the Provider Vault and call Kimss via OpenAI-compat `/v1` (`model=custom:<id>`).
8. Hermis / HTTP interceptors: forward Agent-Id headers; never strip them.
9. Zero-code option: `OPENAI_BASE_URL=https://api.kimss.ai/v1` and `OPENAI_API_KEY=kimss_...` (still set Agent-Id when the client supports default headers).
10. Kill switch: HTTP 403 with `error.code` or `detail.error` = `agent_disabled`.
11. Keys are `kimss_...`, never `km_live_...`.

Canonical rules: [AI_INTEGRATION.md](../AI_INTEGRATION.md). Dense HTTP map: [llm-context.md](llm-context.md). Human guide: [GETTING_STARTED.md](../GETTING_STARTED.md).
