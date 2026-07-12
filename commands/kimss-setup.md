---
name: kimss-setup
description: Verify Kimss MCP configuration (uvx, KIMSS_API_KEY, KIMSS_BASE_URL) and outline a safe smoke test.
---

# Kimss MCP setup check

1. **Confirm transport:** User should have `uvx` on PATH, or `kimss-mcp-server` after `pip install 'kimss[mcp]'`.
2. **Confirm env:** `KIMSS_API_KEY` is set in the MCP server environment (never in repo). Optional `KIMSS_BASE_URL` (`https://api.kimss.ai` or `https://stg.kimss.ai`). Optional `KIMSS_WORKSPACE_ID` for workspace scoping.
3. **Confirm config location:** Cursor uses project or user MCP config; this repo ships root `mcp.json` as a reference template — merge the `kimss` block into the user’s effective MCP config if they are not loading repo-level MCP automatically.
4. **Smoke test (after MCP is running):** Invoke `kimss_run_agent` with a valid `assistant_id` the user owns and a short `message`; capture `conversation_id` for a second turn. If no agent id yet, use `kimss_create_agent` only if their key has management scope.
5. **If startup fails:** Read stderr for `KIMSS_API_KEY`; see [docs/llm-context.md](../docs/llm-context.md) error table for HTTP-layer issues.
