# Changelog

All notable changes to the **kimss** PyPI package are documented here. The canonical source for this file in development is the monorepo path `kimss_sdk/CHANGELOG.md`.

## [2.0.0] — 2026-06-03

### Breaking

- **Python parameters:** `thread_id` was renamed to **`conversation_id`** everywhere in the public SDK (`KimssClient.chat`, `Agent.query`, `client.agents.run`, and MCP tool arguments `kimss_chat` / `kimss_run_agent`). Integrators must rename keyword arguments; positional usage of the second message argument is unchanged for `agents.run(assistant_id, message, ...)`.
- **Semantics:** Kimss agent execution is backed by **Azure AI Foundry 2.x** — **conversations** and the **Responses** API replace classic **threads / runs** shapes. The HTTP JSON field on the wire remains **`thread_id`** (historical name) for the Foundry conversation id; the SDK maps **`conversation_id`** → `thread_id` in request bodies.
- **`AgentRunResult`:** Prefer **`.conversation_id`** for the id returned in `res` (still often keyed as `thread_id` in JSON until a future API revision). Typed access clarifies that this is a **conversation** id, not a legacy Assistants “thread” object.

### Non-breaking

- **Wire format:** No change required to Kimss REST bodies if you call the API directly — `thread_id` in JSON is still the field name for continuing a conversation.

## [1.1.0] and earlier

See [GitHub releases](https://github.com/eyal81/kimss-python-sdk/releases) for older package history on the public mirror.
