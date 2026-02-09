# Kimss Python SDK

Lightweight client for the [Kimss](https://kimss.ai) API. Use it to call your Kimss agents from Python scripts, backends, or notebooks.

## Install

```bash
pip install kimss
```

Or from this repo (editable):

```bash
cd kimss_sdk && pip install -e .
```

## Authentication

Use a **long-lived API key** (not a browser session token). Create keys in your Kimss app under **Developer Settings → API Keys**. The key is scoped to your tenant and user.

## Usage

```python
from kimss import KimssClient, Agent

client = KimssClient(
    api_key="kimss_xxxxxxxxxxxxxxxxxxxxxxxx",  # from Developer Settings
    base_url="https://api.kimss.ai",          # or your deployment URL
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

- **`KimssClient(api_key, base_url="https://api.kimss.ai")`** – authenticated client.
- **`client.get_agent(agent_id)`** – returns an `Agent` for that assistant.
- **`agent.query(message, thread_id=None, chat_type="user_chat")`** – send a message; returns the `res` object from `POST /assistant_chat/`.
- **`client.chat(assistant_id, message, thread_id=None, chat_type="user_chat")`** – one-off chat without an Agent handle.

All requests use the `X-Kimss-Key` header. No streaming in this version; responses are full JSON.
