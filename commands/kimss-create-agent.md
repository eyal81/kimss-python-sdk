---
name: kimss-create-agent
description: Guided flow to create a Kimss agent (management-scoped API key) and send a first message via MCP or SDK.
---

# Kimss — create agent and first run

1. **Prerequisites:** User has a Kimss API key with **management** scope (required for `POST /v1/agents/create` / `kimss_create_agent`). Personal keys without management cannot create agents via API.
2. **Collect inputs:** Display name, optional model deployment id, optional instructions/metadata.
3. **Create:** Call MCP tool `kimss_create_agent` with at least `name`, or SDK `client.agents.create(...)`. Persist returned `assistant_id` (and any `thread_id` / conversation hints returned by the API).
4. **First run:** Call `kimss_run_agent` with `assistant_id`, `message`, no `conversation_id` yet — or SDK `client.agents.run(assistant_id, message, stream=False)`.
5. **Threading:** Store `conversation_id` from the result; pass it on follow-up calls as `conversation_id` (MCP) / same in SDK (maps to JSON `thread_id`).
6. **If 403:** Key scope or agent ownership — do not retry with the same key; explain management scope or use an existing owned `assistant_id`.
