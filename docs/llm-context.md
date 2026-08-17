# Kimss Python SDK — LLM / IDE context

This file is optimized for AI assistants (Cursor, Windsurf, Claude Desktop, Copilot). Pair with the human-oriented [README.md](../README.md) and the refactor spec [KIMSS_ONBOARDING.md](KIMSS_ONBOARDING.md).

## Clean machine checklist (do this first)

1. **Python ≥ 3.10** available.
2. Install the SDK only: `pip install kimss`  
   Declared runtime dep: `requests>=2.28` (pulls urllib3, certifi, charset-normalizer, idna).  
   Do **not** invent packages like `@kimss/sdk` or require azure-identity for API-key auth.
3. Set env: `KIMSS_API_KEY` (required). Optional: `KIMSS_BASE_URL` (default `https://api.kimss.ai`).
4. Preferred first call: `client.agents.get(assistant_id).run("Hello!", stream=False)` or `client.agents.run(assistant_id, "Hello!", stream=False)` → `POST /v1/agents/run`.
5. Auth header for API keys: **`X-Kimss-Key`** — never `Authorization: Bearer` for Kimss API keys.
6. Java customers: JDK 11+ `HttpClient` + `X-Kimss-Key`, or Maven `ai.kimss:kimss-java` when published. No Node SDK — use `fetch` + `X-Kimss-Key`.

## Authentication

### API key (default for scripts and MCP)

- Header: `X-Kimss-Key: <api_key>`
- Create keys in the Kimss app: **Developer Settings → API Keys**.
- **MCP server** reads `KIMSS_API_KEY` from the environment only — do not pass secrets on the CLI or log them.

### Microsoft Entra ID (headless workers)

- Header: `Authorization: Bearer <token>` from `credential.get_token(scope)`.
- `KimssClient(credential=..., token_scope="api://<kimss-api-app-id>/.default", workspace_id=...)`
- Scope can also come from env: `KIMSS_API_SCOPE` or `KIMSS_TOKEN_SCOPE`.
- Optional: `KIMSS_WORKSPACE_ID` → `X-Workspace-ID` header and `tenant_id` in JSON bodies when missing.

### Key prefixes / scopes

The SDK does not parse key prefixes; permissions are enforced by Kimss for the key you created. Treat every key as sensitive. Use least-privilege keys for automation.

## Base URLs

| Environment | URL |
|-------------|-----|
| Production | `https://api.kimss.ai` (no trailing slash) |
| Staging | `https://stg.kimss.ai` |

Override with `KimssClient(..., base_url=...)` or `KIMSS_BASE_URL` for MCP.

## SDK method → HTTP endpoint map

| SDK surface | HTTP | Notes |
|-------------|------|-------|
| `KimssClient.chat` / `Agent.query` | `POST /v1/agents/run` | Same route as **`agents.run`**. Body: `assistant_id`, `usr_chat`, `chat_type`; optional **`thread_id`**. SDK kwarg: **`conversation_id`**. |
| `KimssClient.add_function_to_agent` / `Agent.add_function` | `POST /agent_add_function/` | `assistant_id`, `name`, `description`, `parameters` (JSON Schema object) |
| `KimssClient.agents.create` | `POST /v1/agents/create` | Management; requires privileged key |
| `KimssClient.agents.register` | `POST /v1/agents/register` | Register a customer-owned agent (inventory only; management scope) |
| `KimssClient.usage.report` | `POST /v1/usage/events` | Self-reported BYO token usage (run scope). Prefer `stream_options.include_usage` on the customer's LLM client. |
| `KimssClient.agents.get` / `Agent.run` | `POST /v1/agents/run` | Local handle; `run` is the preferred call |
| `KimssClient.agents.run(..., stream=False)` | `POST /v1/agents/run` | **Preferred** non-streaming agent run; returns **`AgentRunResult`** (dict + **`.text`**, **`.usage.total_credits`**, **`.conversation_id`**) when `res` is a dict. Aliases **`agent_id`/`prompt`**; optional **`conversation_id`** (JSON `thread_id`), **`tags`**, **`routing_preference`** |
| `KimssClient.models.create(..., stream=False)` | `POST /v1/models/completions` | Non-streaming completions (`{"res": ...}` envelope). Optional client ``agent_id`` / env ``KIMSS_AGENT_ID`` → ``X-Kimss-Agent-Id`` (telemetry + kill switch). |
| `KimssClient.images.generate` | `POST /v1/images/generations` | OpenAI-compatible image gen (`data[].b64_json`); feature-gated — 404 `feature_disabled` when off |
| `KimssClient.files.upload` | `POST /v1/files/upload` | Multipart `file` (ephemeral attachments, not RAG) |
| *(OpenAI clients / OmniRoute / Cursor)* | `GET /v1/models` | OpenAI list; `id` = `logical_id` when set (e.g. `gpt-5.6-sol`) |
| *(OpenAI clients / OmniRoute / Cursor)* | `POST /v1/chat/completions` | Bare OpenAI `chat.completion` / chunk SSE; auth `Bearer kimss_...` or `X-Kimss-Key` |

Streaming (`stream=True`) returns an SSE iterator; **MCP tools in v1 are non-streaming only**.

### OpenAI-compatible base URL

```text
base_url = https://api.kimss.ai/v1
api_key  = kimss_...          # Authorization: Bearer or X-Kimss-Key
model    = gpt-5.6-sol        # logical_id preferred
```

Same Foundry deployments and credit pool as `/v1/models/completions`. Do **not** use the App Service hostname.

## Agent / conversation state machine

1. **First message**: call `agents.run("asst_id", "hello", stream=False)` (or `chat` / `query`) with **no** `conversation_id`.
2. **Response** includes the Foundry conversation id in `res`, typically under **`thread_id`** until the API is renamed; the SDK exposes it as **`AgentRunResult.conversation_id`** for `/v1/agents/run`.
3. **Follow-up**: pass the same id as **`conversation_id`** on the next SDK call (serialized as JSON **`thread_id`**).
4. **Ephemeral attachments**: upload via `files.upload` (`POST /v1/files/upload`) for a single chat/completion turn (vision / document parse). Kimss does **not** host vector stores or RAG indexes — retrieve on your side and pass augmented messages through the gateway. Hosted `/v1/vector_stores/*` returns **410** `rag_deprecated`.

## Error code dictionary (typed SDK exceptions)

Errors are raised via `raise_for_kimss_error` into subclasses of `KimssApiError`. JSON bodies use FastAPI-style `{"detail": {"error": "<code>", "message": "..."}}`.

| HTTP | `detail.error` | Exception | Meaning / assistant behavior |
|------|----------------|-----------|------------------------------|
| 403 | `subscription_required` | `KimssSubscriptionRequired` | Workspace needs paid entitlement — do not retry; tell the user to upgrade or switch workspace. |
| 429 | `governed_requests_exhausted` | `KimssGovernedRequestsExhausted` | Monthly governed-request allowance reached (free tier: 25,000/mo) — do not tight-loop retry; meter resets next month; suggest upgrade. `detail` has `used`, `included`, `year_month`. |
| 429 | `credit_pool_exhausted` | `KimssCreditExhausted` | Monthly pool exhausted — do not tight-loop retry; surface to user; backoff hours/days. |
| 429 | `individual_free_trial_exhausted` | `KimssCreditExhausted` | Trial cap hit — same as above. |
| 429 | `credit_policy_blocked` | `KimssCreditExhausted` | Policy blocked usage — surface `detail`; no blind retry. |
| 429 | `rate_limit_exceeded` | `KimssRateLimited` | Short-term rate limit — honor `Retry-After` if present; exponential backoff; retry is OK after delay. |
| other 4xx/5xx | (varies) | `requests.HTTPError` | Log `response.text` safely; do not assume shape. |

The HTTP client **retries 5xx** with urllib3 `Retry` (not 429).

## MCP tools (stdio)

Install: `pip install 'kimss[mcp]'`. Run: `kimss-mcp-server` with `KIMSS_API_KEY` set.

**Clients:** Cursor / Windsurf (`mcpServers` JSON), Claude Desktop (`claude_desktop_config.json` via **Settings → Developer → Edit Config**). Preferred zero-venv launch: `uvx --from kimss[mcp] kimss-mcp-server` (not `--with`).

| Tool | Purpose |
|------|---------|
| `kimss_chat` | `POST /v1/agents/run` |
| `kimss_create_agent` | `POST /v1/agents/create` |
| `kimss_run_agent` | `POST /v1/agents/run` (non-stream) |
| `kimss_complete` | `POST /v1/models/completions` (non-stream) |
| `kimss_upload_file` | `POST /v1/files/upload` |
| `kimss_add_function_to_agent` | `POST /agent_add_function/` |

On Kimss API errors, tools raise **RuntimeError** whose message is a JSON string: `{"kind":"kimss_api_error","http_status",...}` — parse for defensive handling.

## Usage Hub header

For agent/model calls the SDK may send `X-Kimss-SDK-Context` (telemetry). See README **Usage Hub** section to strip via `before_request_hooks` if paths must not leave the process.
