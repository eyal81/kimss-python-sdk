---
name: kimss-mcp-setup
description: Configure the Kimss MCP server in Cursor, Windsurf, Claude Desktop, or other MCP clients using uvx, environment variables, and the seven v1 tools.
---

# Kimss MCP setup

## When to use

- User asks how to wire Kimss into Cursor, Windsurf, Claude Desktop, or another MCP client.
- Debugging MCP startup (missing API key, wrong base URL, tools not listed).

## Requirements

- `uv` / `uvx` **or** `pip install 'kimss[mcp]'` so `kimss-mcp-server` is available.
- Long-lived **Kimss API key** from the app: **Developer Settings → API Keys** (never commit it).

## Cursor / generic `mcp.json`

```json
{
  "mcpServers": {
    "kimss": {
      "command": "uvx",
      "args": ["--from", "kimss[mcp]", "kimss-mcp-server"],
      "env": {
        "KIMSS_API_KEY": "your_key_here",
        "KIMSS_BASE_URL": "https://api.kimss.ai"
      }
    }
  }
}
```

- Set `KIMSS_API_KEY` in the IDE environment or user secrets — not in the repo.
- Optional: `KIMSS_WORKSPACE_ID` for workspace-scoped calls.
- Prefer `uvx --from kimss[mcp] kimss-mcp-server` (not `--with`).

## Claude Desktop (`claude_desktop_config.json`)

1. **Settings → Developer → Edit Config** (opens the correct file for the install).
2. Merge the same `kimss` `mcpServers` block as above.
3. Fully quit and relaunch Claude Desktop; confirm tools appear in the MCP/hammer UI.

Typical paths (prefer Edit Config over guessing):

| OS | Path |
|----|------|
| macOS | `~/Library/Application Support/Claude/claude_desktop_config.json` |
| Windows (classic) | `%APPDATA%\Claude\claude_desktop_config.json` |
| Linux | `~/.config/Claude/claude_desktop_config.json` |

## Installed package alternative

After `pip install 'kimss[mcp]'`:

```json
"command": "kimss-mcp-server",
"args": [],
"env": { "KIMSS_API_KEY": "...", "KIMSS_BASE_URL": "https://api.kimss.ai" }
```

## MCP tools (v1, non-streaming)

| Tool | Backend (summary) |
|------|-------------------|
| `kimss_chat` | `POST /assistant_chat/` |
| `kimss_run_agent` | `POST /v1/agents/run` |
| `kimss_create_agent` | `POST /v1/agents/create` (management-scoped key) |
| `kimss_complete` | `POST /v1/models/completions` |
| `kimss_upload_file` | `POST /v1/files/upload` |
| `kimss_create_vector_store` | `POST /v1/vector_stores/create` |
| `kimss_add_function_to_agent` | `POST /agent_add_function/` |

Argument JSON schemas are defined in `kimss/mcp/tools.py` (`TOOL_INPUT_SCHEMAS`).

## Troubleshooting

- **Process exits immediately:** `KIMSS_API_KEY` unset or empty — set env and restart MCP / Claude Desktop.
- **Claude Desktop ignores edits:** wrong config path (especially Windows MSIX) — use **Settings → Developer → Edit Config**.
- **404 / feature_disabled:** gateway feature not enabled for the workspace or environment — check Kimss admin / plan; do not switch to non-canonical API URLs.
- **403 on create/update tools:** key lacks **management** scope or agent is not owned — use an appropriate key or owned agent id.

## Reference

- [README.md](../../README.md) — Cursor, Windsurf, and Claude Desktop blocks.
- [docs/llm-context.md](../../docs/llm-context.md) — MCP table and auth.
