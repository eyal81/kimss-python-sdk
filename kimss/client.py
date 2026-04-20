"""
Kimss API client and Agent wrapper.
Use X-Kimss-Key for authentication (long-lived API key from your Kimss Developer Settings).
"""
from __future__ import annotations

import logging
from typing import Any, Callable, Dict, List, MutableMapping, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .privacy import BeforeRequestHook

logger = logging.getLogger(__name__)


def _normalize_parameters(parameters: Any) -> Dict[str, Any]:
    """Ensure parameters is a JSON-schema dict for the function tool."""
    if parameters is None:
        return {"type": "object", "properties": {}, "additionalProperties": False}
    if isinstance(parameters, dict):
        return parameters
    return dict(parameters)


def _default_retry() -> Retry:
    return Retry(
        total=4,
        connect=3,
        read=3,
        status=3,
        backoff_factor=0.6,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset({"POST", "GET"}),
        raise_on_status=False,
        respect_retry_after_header=True,
    )


class KimssClient:
    """
    Client for the Kimss API. Authenticate with a long-lived API key.
    Create keys at: your Kimss app → Developer Settings → API Keys.
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.kimss.ai",
        *,
        before_request_hooks: Optional[List[BeforeRequestHook]] = None,
        privacy: Any = None,
        session: Optional[requests.Session] = None,
        retry: Optional[Retry] = None,
    ):
        """
        api_key: From Kimss app → Developer Settings → API Keys.
        base_url: Your actual Kimss API URL (e.g. https://your-app.azurewebsites.net).
        before_request_hooks: Optional callables invoked as hook(ctx) where ctx is
            {"path": str, "json": dict, "headers": dict}; hooks may mutate json/headers.
        privacy: Optional PresidioRedactor (or any BeforeRequestHook) appended to hooks.
        session: Optional shared requests.Session (e.g. for tests).
        retry: Optional urllib3.Retry for 429/5xx (default respects Retry-After).
        """
        self.api_key = api_key.strip()
        self.base_url = base_url.rstrip("/")
        self.headers: Dict[str, str] = {
            "X-Kimss-Key": self.api_key,
            "Content-Type": "application/json",
        }
        self._hooks: List[BeforeRequestHook] = list(before_request_hooks or [])
        if privacy is not None:
            self._hooks.append(privacy)
        self._session = session or requests.Session()
        adapter = HTTPAdapter(max_retries=retry or _default_retry())
        self._session.mount("https://", adapter)
        self._session.mount("http://", adapter)

    def _post_json(self, path: str, json_body: Dict[str, Any], timeout: int) -> requests.Response:
        ctx: Dict[str, Any] = {
            "path": path,
            "json": json_body,
            "headers": dict(self.headers),
        }
        for hook in self._hooks:
            try:
                hook(ctx)
            except Exception:
                logger.exception("before_request hook failed path=%s", path)
                raise
        url = f"{self.base_url}{path}"
        return self._session.post(
            url,
            json=ctx["json"],
            headers=ctx["headers"],
            timeout=timeout,
        )

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

    def add_function_to_agent(
        self,
        agent_id: str,
        name: str,
        description: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Add a function tool definition to an agent (owned by the API key user).
        """
        payload: Dict[str, Any] = {
            "assistant_id": agent_id,
            "name": name.strip(),
            "description": (description or "").strip(),
            "parameters": _normalize_parameters(parameters),
        }
        response = self._post_json("/agent_add_function/", payload, timeout=60)
        response.raise_for_status()
        data = response.json()
        return data.get("res", data)


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
        """
        payload: Dict[str, Any] = {
            "assistant_id": self.id,
            "usr_chat": message,
            "chat_type": chat_type,
        }
        if thread_id is not None and str(thread_id).strip():
            payload["thread_id"] = str(thread_id).strip()
        response = self._client._post_json("/assistant_chat/", payload, timeout=120)
        response.raise_for_status()
        data = response.json()
        return data.get("res", data)

    def add_function(
        self,
        name: str,
        description: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Add a function tool definition to this agent."""
        return self._client.add_function_to_agent(
            self.id, name, description or "", parameters
        )
