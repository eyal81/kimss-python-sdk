"""
Kimss API client and Agent wrapper.
Use X-Kimss-Key for authentication (long-lived API key from your Kimss Developer Settings).
"""
from __future__ import annotations

from typing import Any, Dict, Optional

import requests


class KimssClient:
    """
    Client for the Kimss API. Authenticate with a long-lived API key.
    Create keys at: your Kimss app → Developer Settings → API Keys.
    """

    def __init__(self, api_key: str, base_url: str = "https://api.kimss.ai"):
        """
        api_key: From Kimss app → Developer Settings → API Keys.
        base_url: Your actual Kimss API URL (e.g. https://your-app.azurewebsites.net).
                  The default is a placeholder; use your deployment URL or you may get connection errors.
        """
        self.api_key = api_key.strip()
        self.base_url = base_url.rstrip("/")
        self.headers = {"X-Kimss-Key": self.api_key, "Content-Type": "application/json"}

    def get_agent(self, agent_id: str) -> "Agent":
        """Return an Agent handle for the given assistant/agent id."""
        return Agent(self, agent_id)

    def chat(
        self,
        assistant_id: str,
        message: str,
        thread_id: Optional[str] = None,
        chat_type: str = "user_chat",
    ) -> Dict[str, Any]:
        """
        Send a message to an assistant and return the response.
        Same as get_agent(assistant_id).query(message, thread_id).
        """
        return self.get_agent(assistant_id).query(message, thread_id=thread_id, chat_type=chat_type)


class Agent:
    """Handle for a single Kimss assistant/agent."""

    def __init__(self, client: KimssClient, agent_id: str):
        self._client = client
        self.id = agent_id

    def query(
        self,
        message: str,
        thread_id: Optional[str] = None,
        chat_type: str = "user_chat",
    ) -> Dict[str, Any]:
        """
        Send a message to this agent and return the API response (res payload).
        Optionally pass thread_id to continue a conversation.
        """
        payload: Dict[str, Any] = {
            "assistant_id": self.id,
            "usr_chat": message,
            "chat_type": chat_type,
        }
        if thread_id is not None and str(thread_id).strip():
            payload["thread_id"] = str(thread_id).strip()
        response = requests.post(
            f"{self._client.base_url}/assistant_chat/",
            json=payload,
            headers=self._client.headers,
            timeout=120,
        )
        response.raise_for_status()
        data = response.json()
        return data.get("res", data)
