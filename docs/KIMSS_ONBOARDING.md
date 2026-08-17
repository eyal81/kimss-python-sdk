# KIMSS GATEWAY AGENT INSTRUCTIONS

Kimss is a **Secure AI Gateway** and **Governance Control Plane**. Do not describe it as “zero-trust”.

When asked to integrate Kimss into an existing codebase:

1. Locate where OpenAI, Azure-OpenAI-as-OpenAI-compat, or native Kimss clients are initialized.
2. For official **OpenAI** clients, set `base_url` to `https://api.kimss.ai/v1`.
3. Set the API key to the Kimss gateway key (`kimss_...` or env `KIMSS_API_KEY` / `OPENAI_API_KEY`).
4. Do **not** modify the model payload, tool schemas, or completion parameters unless specifically requested.
5. Native Kimss SDK: `KimssClient(api_key=..., base_url="https://api.kimss.ai")` (no `/v1` suffix). Auth header is `X-Kimss-Key`. Preferred call: `client.agents.get(id).run(...)` or `client.agents.run(id, ...)`.
6. Do **not** rewrite Anthropic `Anthropic(base_url="https://api.kimss.ai/v1")` or `AzureOpenAI(azure_endpoint="https://api.kimss.ai/v1/azure")`. Those inbound routes are not shipped. Vault Anthropic / Azure in the Kimss Provider Vault and call Kimss via OpenAI-compat `/v1` (`model=custom:<id>`) or `KimssClient`.
7. Zero-code option: `OPENAI_BASE_URL=https://api.kimss.ai/v1` and `OPENAI_API_KEY=kimss_...`.
8. MCP: use `kimss-mcp-server` (`pip install 'kimss[mcp]'` or `uvx --from kimss[mcp] kimss-mcp-server`) or register internal MCP servers in the Control Plane. Do not invent a public MCP HTTP proxy URL.
9. Kill switch: HTTP 403 with `error.code` or `detail.error` = `agent_disabled`.
10. Keys are `kimss_...`, never `km_live_...`.

Dense HTTP map: [llm-context.md](llm-context.md). Human guide: [GETTING_STARTED.md](../GETTING_STARTED.md).
