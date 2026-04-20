# Kimss Python SDK

Lightweight client for the [Kimss](https://kimss.ai) API. Use it to call your Kimss agents from Python scripts, backends, or notebooks.

## Install

```bash
pip install kimss
```

Optional **PII redaction** (Microsoft Presidio + spaCy model, e.g. `python -m spacy download en_core_web_lg`):

```bash
pip install 'kimss[privacy]'
```

Or from this repo (editable):

```bash
cd kimss_sdk && pip install -e .
```

## Authentication

Use a **long-lived API key** (not a browser session token). Create keys in your Kimss app under **Developer Settings → API Keys**. The key is scoped to your tenant and user.

## Usage

Pass your **actual API base URL** (the one your Kimss provider gave you). The default `https://api.kimss.ai` is only a placeholder — set `base_url` or you will get connection errors.

- **Prefer the APIM gateway URL** if your provider uses one (e.g. `https://xxx.azure-api.net`): one stable URL for all users.
- Backend URLs (e.g. `...azurewebsites.net`) are per deployment; not the same for every user.

```python
from kimss import KimssClient, Agent

client = KimssClient(
    api_key="kimss_xxxxxxxxxxxxxxxxxxxxxxxx",  # from Developer Settings
    base_url="https://your-apim.azure-api.net",  # or the URL your provider gave you (no trailing slash)
)

# Get an agent and send a message
agent = client.get_agent(agent_id="asst_xxxx")
result = agent.query("Hello")
# result is the API "res" payload (run_id, thread_id, messages, usage, etc.)

# Continue a thread
result2 = agent.query("What did I just say?", thread_id=result.get("thread_id"))

# Or use the client directly
result3 = client.chat(assistant_id="asst_xxxx", message="Hi", thread_id=result.get("thread_id"))
```

## API

- **`KimssClient(api_key, base_url="...", before_request_hooks=None, privacy=None, session=None, retry=None)`** – authenticated client. `base_url` must be your real Kimss API (e.g. Azure or APIM URL). Uses a `requests.Session` with **retry on 429 / 5xx** and **Retry-After** by default.
- **`client.get_agent(agent_id)`** – returns an `Agent` for that assistant.
- **`agent.query(message, thread_id=None, chat_type="user_chat")`** – send a message; returns the `res` object from `POST /assistant_chat/`.
- **`client.chat(assistant_id, message, thread_id=None, chat_type="user_chat")`** – one-off chat without an Agent handle.
- **`before_request_hooks`** – list of callables `hook(ctx)` where `ctx` is `{"path": str, "json": dict, "headers": dict}`; hooks may mutate `json` / `headers` before the HTTP POST.
- **`privacy`** – shortcut for `PresidioRedactor()` from `kimss.privacy` (requires `kimss[privacy]`).

```python
from kimss import KimssClient, PresidioRedactor

client = KimssClient(
    api_key="kimss_...",
    base_url="https://your-apim.azure-api.net",
    privacy=PresidioRedactor(),
)
```

All requests use the `X-Kimss-Key` header. No streaming in this version; responses are full JSON.
