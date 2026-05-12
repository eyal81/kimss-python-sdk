"""
Kimss API client and Agent wrapper.
Use X-Kimss-Key for authentication (long-lived API key from your Kimss Developer Settings).
"""
from __future__ import annotations

import logging
import os
from typing import Any, Callable, Dict, Generator, List, MutableMapping, Optional, Union, Iterator

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .privacy import BeforeRequestHook
from .telemetry.context import encode_sdk_context_header_value

logger = logging.getLogger(__name__)


def _normalize_parameters(parameters: Any) -> Dict[str, Any]:
    """Ensure parameters is a JSON-schema dict for the function tool."""
    if parameters is None:
        return {"type": "object", "properties": {}, "additionalProperties": False}
    if isinstance(parameters, dict):
        return parameters
    return dict(parameters)


def _sdk_resource_meta(path: str, json_body: Dict[str, Any]) -> Optional[tuple]:
    """Return (resource_type, resource_name) for Usage Hub context, or None to skip header."""
    p = (path or "").lower()
    jb = json_body or {}
    if "/v1/models/completions" in p:
        return ("model", str(jb.get("model") or "").strip())
    if "/v1/agents/run" in p or "/assistant_chat" in p:
        return ("agent", str(jb.get("assistant_id") or "").strip())
    if "/agent_add_function" in p:
        return ("agent", str(jb.get("assistant_id") or "").strip())
    return None


def _attach_sdk_context_header(headers: MutableMapping[str, str], path: str, json_body: Dict[str, Any]) -> None:
    meta = _sdk_resource_meta(path, json_body)
    if not meta:
        return
    rt, rn = meta
    try:
        headers["X-Kimss-SDK-Context"] = encode_sdk_context_header_value(resource_type=rt, resource_name=rn)
    except Exception:
        logger.debug("sdk context header skipped path=%s", path, exc_info=True)


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
        api_key: Optional[str] = None,
        base_url: str = "https://api.kimss.ai",
        *,
        credential: Any = None,
        token_scope: Optional[str] = None,
        workspace_id: Optional[str] = None,
        before_request_hooks: Optional[List[BeforeRequestHook]] = None,
        privacy: Any = None,
        session: Optional[requests.Session] = None,
        retry: Optional[Retry] = None,
    ):
        """
        api_key: From Kimss app → Developer Settings → API Keys.
        credential: Optional Azure credential with get_token(scope) for headless
            Entra ID auth. When set, requests use Authorization: Bearer.
        token_scope: Scope used with credential.get_token(...), e.g.
            api://<kimss-api-app-id>/.default. Defaults to KIMSS_API_SCOPE
            or KIMSS_TOKEN_SCOPE when present.
        workspace_id: Optional tenant/workspace key to stamp onto request
            headers and JSON bodies as tenant_id.
        base_url: Kimss API URL. Use https://api.kimss.ai for production.
        before_request_hooks: Optional callables invoked as hook(ctx) where ctx is
            {"path": str, "json": dict, "headers": dict}; hooks may mutate json/headers.
        privacy: Optional PresidioRedactor (or any BeforeRequestHook) appended to hooks.
        session: Optional shared requests.Session (e.g. for tests).
        retry: Optional urllib3.Retry for 429/5xx (default respects Retry-After).
        """
        self.api_key = (api_key or "").strip()
        self._credential = credential
        self._token_scope = (
            token_scope
            or os.getenv("KIMSS_API_SCOPE")
            or os.getenv("KIMSS_TOKEN_SCOPE")
            or ""
        ).strip()
        self.workspace_id = (workspace_id or os.getenv("KIMSS_WORKSPACE_ID") or "").strip()
        if not self.api_key and self._credential is None:
            raise ValueError("KimssClient requires either api_key or credential")
        if self._credential is not None and not self._token_scope:
            raise ValueError(
                "KimssClient credential auth requires token_scope or KIMSS_API_SCOPE"
            )
        self.base_url = base_url.rstrip("/")
        self.headers: Dict[str, str] = {"Content-Type": "application/json"}
        if self.api_key:
            self.headers["X-Kimss-Key"] = self.api_key
        if self.workspace_id:
            self.headers["X-Workspace-ID"] = self.workspace_id
        self._hooks: List[BeforeRequestHook] = list(before_request_hooks or [])
        if privacy is not None:
            self._hooks.append(privacy)
        self._session = session or requests.Session()
        adapter = HTTPAdapter(max_retries=retry or _default_retry())
        self._session.mount("https://", adapter)
        self._session.mount("http://", adapter)
        self.models = ModelsNamespace(self)
        self.agents = AgentsRunV1(self)
        self.vector_stores = VectorStoresNamespace(self)
        self.files = FilesNamespace(self)

    def _request_headers(self, *, include_content_type: bool = True) -> Dict[str, str]:
        headers = dict(self.headers)
        if not include_content_type:
            headers = {k: v for k, v in headers.items() if k.lower() != "content-type"}
        if self._credential is not None:
            token = self._credential.get_token(self._token_scope)
            headers["Authorization"] = f"Bearer {token.token}"
            headers.pop("X-Kimss-Key", None)
        return headers

    def _post_json(self, path: str, json_body: Dict[str, Any], timeout: int) -> requests.Response:
        body = dict(json_body)
        if self.workspace_id and not str(body.get("tenant_id") or "").strip():
            body["tenant_id"] = self.workspace_id
        ctx: Dict[str, Any] = {
            "path": path,
            "json": body,
            "headers": self._request_headers(),
        }
        _attach_sdk_context_header(ctx["headers"], path, body)
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

    def _iter_sse_json(self, response: "requests.Response") -> Generator[Dict[str, Any], None, None]:
        """Parse `data: {...}` lines from a Kimss SSE stream."""
        import json

        for raw in response.iter_lines(decode_unicode=True):
            if not raw or not str(raw).strip():
                continue
            line = str(raw).strip()
            if not line.startswith("data:"):
                continue
            payload = line[5:].strip()
            if payload == "[DONE]":
                break
            try:
                obj = json.loads(payload)
            except Exception:
                continue
            if isinstance(obj, dict):
                yield obj

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


class VectorStoresNamespace:
    """v1 vector store management: POST /v1/vector_stores/create.

    Optional ``agent_id`` links the new store to an existing agent
    (``replace=True`` semantics on the API side).
    """

    def __init__(self, client: KimssClient) -> None:
        self._client = client

    def create(
        self,
        *,
        name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        agent_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a vector store and return its ``res`` payload."""
        payload: Dict[str, Any] = {}
        if name is not None and str(name).strip():
            payload["name"] = str(name).strip()
        if metadata is not None:
            payload["metadata"] = metadata
        if agent_id is not None and str(agent_id).strip():
            payload["agent_id"] = str(agent_id).strip()
        if tenant_id is not None and str(tenant_id).strip():
            payload["tenant_id"] = str(tenant_id).strip()
        r = self._client._post_json("/v1/vector_stores/create", payload, timeout=120)
        r.raise_for_status()
        body = r.json()
        return body.get("res", body)


class FilesNamespace:
    """Upload files for /v1/models/completions attachments."""

    def __init__(self, client: KimssClient) -> None:
        self._client = client

    def upload(
        self,
        path: Union[str, bytes],
        filename: Optional[str] = None,
        *,
        content_type: str = "application/octet-stream",
    ) -> Dict[str, Any]:
        import os

        if isinstance(path, (bytes, bytearray)):
            data = bytes(path)
            fn = filename or "upload"
        else:
            fn = filename or os.path.basename(str(path))
            with open(path, "rb") as f:  # noqa: SIM115
                data = f.read()
        url = f"{self._client.base_url}/v1/files/upload"
        h = self._client._request_headers(include_content_type=False)
        r = self._client._session.post(
            url,
            files={"file": (fn, data, content_type)},
            headers=h,
            timeout=60,
        )
        r.raise_for_status()
        body = r.json()
        return body.get("res", body)


class ModelsNamespace:
    """Standard (non-agent) model completions: POST /v1/models/completions."""

    def __init__(self, client: KimssClient) -> None:
        self._client = client

    def create(
        self,
        model: str,
        messages: List[Dict[str, str]],
        *,
        stream: bool = False,
        system: Optional[str] = None,
        attachments: Optional[List[Dict[str, str]]] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> Union[Dict[str, Any], Generator[Dict[str, Any], None, None]]:
        payload: Dict[str, Any] = {
            "model": model,
            "messages": messages,
            "stream": stream,
        }
        if system is not None:
            payload["system"] = system
        if attachments:
            payload["attachments"] = attachments
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        if temperature is not None:
            payload["temperature"] = temperature
        if not stream:
            r = self._client._post_json("/v1/models/completions", payload, timeout=120)
            r.raise_for_status()
            return r.json().get("res", r.json())
        if self._client.workspace_id and not str(payload.get("tenant_id") or "").strip():
            payload = dict(payload)
            payload["tenant_id"] = self._client.workspace_id
        ctx: Dict[str, Any] = {
            "path": "/v1/models/completions",
            "json": payload,
            "headers": self._client._request_headers(),
        }
        _attach_sdk_context_header(ctx["headers"], "/v1/models/completions", payload)
        for hook in self._client._hooks:
            try:
                hook(ctx)
            except Exception:
                logger.exception("before_request hook failed path=v1/models/completions")
                raise
        url = f"{self._client.base_url}/v1/models/completions"
        response = self._client._session.post(
            url, json=ctx["json"], headers=ctx["headers"], stream=True, timeout=300
        )
        response.raise_for_status()

        def _gen() -> Generator[Dict[str, Any], None, None]:
            yield from self._client._iter_sse_json(response)

        return _gen()


class AgentsRunV1:
    """v1 agent management + orchestration.

    - ``create`` -> POST /v1/agents/create (management API key scope or Entra
      Bearer with equivalent privileges). Returns the inner ``res`` payload
      (e.g. ``{"assistant_id": "...", "agent_name": "..."}``).
    - ``run``    -> POST /v1/agents/run   (orchestration; replaces /assistant_chat
      for new integrations).
    """

    def __init__(self, client: KimssClient) -> None:
        self._client = client

    def create(
        self,
        *,
        name: str,
        model: Optional[str] = None,
        instructions: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        owner_id: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        tenant_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a Foundry-backed Kimss agent and return its ``res`` payload."""
        payload: Dict[str, Any] = {"name": (name or "").strip()}
        if not payload["name"]:
            raise ValueError("agents.create requires a non-empty name")
        if model is not None and str(model).strip():
            payload["model"] = str(model).strip()
        if instructions is not None:
            payload["instructions"] = instructions
        if metadata is not None:
            payload["metadata"] = metadata
        if owner_id is not None and str(owner_id).strip():
            payload["owner_id"] = str(owner_id).strip()
        if tools is not None:
            payload["tools"] = tools
        if tenant_id is not None and str(tenant_id).strip():
            payload["tenant_id"] = str(tenant_id).strip()
        r = self._client._post_json("/v1/agents/create", payload, timeout=120)
        r.raise_for_status()
        body = r.json()
        return body.get("res", body)

    def run(
        self,
        assistant_id: str,
        message: str,
        *,
        stream: bool = False,
        thread_id: Optional[str] = None,
        chat_type: str = "user_chat",
    ) -> Union[Dict[str, Any], Generator[Dict[str, Any], None, None]]:
        payload: Dict[str, Any] = {
            "assistant_id": assistant_id,
            "usr_chat": message,
            "stream": stream,
            "chat_type": chat_type,
        }
        if thread_id:
            payload["thread_id"] = str(thread_id).strip()
        if not stream:
            r = self._client._post_json("/v1/agents/run", payload, timeout=120)
            r.raise_for_status()
            return r.json().get("res", r.json())
        if self._client.workspace_id and not str(payload.get("tenant_id") or "").strip():
            payload = dict(payload)
            payload["tenant_id"] = self._client.workspace_id
        ctx: Dict[str, Any] = {
            "path": "/v1/agents/run",
            "json": payload,
            "headers": self._client._request_headers(),
        }
        _attach_sdk_context_header(ctx["headers"], "/v1/agents/run", payload)
        for hook in self._client._hooks:
            try:
                hook(ctx)
            except Exception:
                logger.exception("before_request hook failed path=v1/agents/run")
                raise
        url = f"{self._client.base_url}/v1/agents/run"
        response = self._client._session.post(
            url, json=ctx["json"], headers=ctx["headers"], stream=True, timeout=300
        )
        response.raise_for_status()

        def _gen() -> Generator[Dict[str, Any], None, None]:
            yield from self._client._iter_sse_json(response)

        return _gen()
