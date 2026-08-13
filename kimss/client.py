"""
Kimss API client and Agent wrapper.
Use X-Kimss-Key for authentication (long-lived API key from your Kimss Developer Settings).
"""
from __future__ import annotations

import json
import logging
import os
from typing import Any, Callable, Dict, Generator, List, MutableMapping, Optional, Union

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .errors import raise_for_kimss_error
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
    if "/v1/agents/run" in p or "/assistant_chat" in p or "/v1/dw/hermis_chat" in p:
        return ("agent", str(jb.get("assistant_id") or jb.get("agent_id") or "").strip())
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
        # Do not retry 429: credit exhaustion and rate limits must surface immediately.
        status_forcelist=(500, 502, 503, 504),
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
        agent_id: Optional[str] = None,
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
        agent_id: Optional registered agent id. Sent as ``X-Kimss-Agent-Id`` so
            completions/chat/images telemetry is attributed to that inventory
            row (and kill-switched when the agent is disabled). Falls back to
            env ``KIMSS_AGENT_ID`` when unset.
        base_url: Kimss API URL. Use https://api.kimss.ai for production.
        before_request_hooks: Optional callables invoked as hook(ctx) where ctx is
            {"path": str, "json": dict, "headers": dict}; hooks may mutate json/headers.
        privacy: Optional PresidioRedactor (or any BeforeRequestHook) appended to hooks.
        session: Optional shared requests.Session (e.g. for tests).
        retry: Optional urllib3.Retry for 5xx (default respects Retry-After; 429 is not retried).
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
        self.agent_id = (agent_id or os.getenv("KIMSS_AGENT_ID") or "").strip()
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
        if self.agent_id:
            self.headers["X-Kimss-Agent-Id"] = self.agent_id
        self._hooks: List[BeforeRequestHook] = list(before_request_hooks or [])
        if privacy is not None:
            self._hooks.append(privacy)
        self._session = session or requests.Session()
        adapter = HTTPAdapter(max_retries=retry or _default_retry())
        self._session.mount("https://", adapter)
        self._session.mount("http://", adapter)
        self.models = ModelsNamespace(self)
        self.agents = AgentsRunV1(self)
        self.dw = DwNamespace(self)
        self.usage = UsageNamespace(self)
        self.vector_stores = VectorStoresNamespace(self)
        self.files = FilesNamespace(self)
        self.images = ImagesNamespace(self)

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
        conversation_id: Optional[str] = None,
        chat_type: str = "user_chat",
    ) -> Dict[str, Any]:
        """
        Send a message to an assistant and return the response.
        Same as get_agent(assistant_id).query(message, conversation_id=...).

        The Kimss HTTP API still uses the JSON field ``thread_id`` for the
        Foundry **conversation** id; the SDK maps ``conversation_id`` to that
        field for clarity (v2+).
        """
        return self.get_agent(assistant_id).query(
            message, conversation_id=conversation_id, chat_type=chat_type
        )

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
        raise_for_kimss_error(response)
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
        conversation_id: Optional[str] = None,
        chat_type: str = "user_chat",
    ) -> Dict[str, Any]:
        """
        Send a message to this agent and return the API response (res payload).

        ``conversation_id`` continues the same Foundry conversation as the
        previous turn (Kimss JSON field ``thread_id`` on the wire).
        """
        payload: Dict[str, Any] = {
            "assistant_id": self.id,
            "usr_chat": message,
            "chat_type": chat_type,
        }
        if conversation_id is not None and str(conversation_id).strip():
            payload["thread_id"] = str(conversation_id).strip()
        response = self._client._post_json("/assistant_chat/", payload, timeout=120)
        raise_for_kimss_error(response)
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
    """v1 vector store management: create + upload files.

    Optional ``agent_id`` on create links the new store to an existing agent
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
        raise_for_kimss_error(r)
        body = r.json()
        return body.get("res", body)

    def upload_file(
        self,
        vector_store_id: str,
        path: Union[str, bytes],
        filename: Optional[str] = None,
        *,
        content_type: str = "application/octet-stream",
    ) -> Dict[str, Any]:
        """Upload a file into an existing vector store (``POST /v1/vector_stores/{id}/files``)."""
        import os

        vsid = str(vector_store_id or "").strip()
        if not vsid:
            raise ValueError("vector_store_id is required")
        if isinstance(path, (bytes, bytearray)):
            data = bytes(path)
            fn = filename or "upload"
        else:
            fn = filename or os.path.basename(str(path))
            with open(path, "rb") as f:  # noqa: SIM115
                data = f.read()
        url = f"{self._client.base_url}/v1/vector_stores/{vsid}/files"
        h = self._client._request_headers(include_content_type=False)
        r = self._client._session.post(
            url,
            files={"file": (fn, data, content_type)},
            headers=h,
            timeout=120,
        )
        raise_for_kimss_error(r)
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
        raise_for_kimss_error(r)
        body = r.json()
        return body.get("res", body)


class ImagesNamespace:
    """Image generation: POST /v1/images/generations (gpt-image-2 family).

    Feature-gated server side (``KIMSS_IMAGES_API_ENABLED``); a 404 with
    ``feature_disabled`` means the gateway has not enabled image generation
    for your environment yet.
    """

    def __init__(self, client: KimssClient) -> None:
        self._client = client

    def generate(
        self,
        prompt: str,
        *,
        model: Optional[str] = None,
        size: Optional[str] = None,
        quality: Optional[str] = None,
        n: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Generate image(s) from a text prompt.

        Args:
            prompt: Text description of the desired image.
            model: Logical model or deployment name (default ``gpt-image-2``).
            size: ``1024x1024`` (default), ``1024x1536``, ``1536x1024``, or ``auto``.
            quality: ``low``, ``medium`` (default), ``high``, or ``auto``.
            n: Number of images (1-4, default 1).

        Returns:
            OpenAI-compatible dict: ``{"created", "model", "data": [{"b64_json", ...}], "usage"}``.
            Decode ``data[0]["b64_json"]`` with :func:`base64.b64decode` to get bytes.
        """
        text = (prompt or "").strip()
        if not text:
            raise ValueError("images.generate requires a non-empty prompt")
        payload: Dict[str, Any] = {"prompt": text}
        if model is not None and str(model).strip():
            payload["model"] = str(model).strip()
        if size is not None:
            payload["size"] = size
        if quality is not None:
            payload["quality"] = quality
        if n is not None:
            payload["n"] = int(n)
        r = self._client._post_json("/v1/images/generations", payload, timeout=300)
        raise_for_kimss_error(r)
        body = r.json()
        return body.get("res", body) if isinstance(body, dict) else body


class ModelsNamespace:
    """Standard (non-agent) model completions: POST /v1/models/completions."""

    def __init__(self, client: KimssClient) -> None:
        self._client = client

    def create(
        self,
        model: str,
        messages: Optional[List[Dict[str, str]]] = None,
        *,
        prompt: Optional[str] = None,
        stream: bool = False,
        system: Optional[str] = None,
        attachments: Optional[List[Dict[str, str]]] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> Union[Dict[str, Any], Generator[Dict[str, Any], None, None]]:
        """Create a model completion.

        Prefer ``messages`` (chat turns). ``prompt`` is accepted as a convenience
        alias for a single user message — Digital Workers / older call sites may
        pass ``prompt=`` the same way as ``agents.run``.
        """
        if messages is None:
            text = (prompt or "").strip()
            if not text:
                raise ValueError("models.create requires messages or a non-empty prompt")
            messages = [{"role": "user", "content": text}]
        elif not isinstance(messages, list) or not messages:
            raise ValueError("models.create messages must be a non-empty list")
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
            raise_for_kimss_error(r)
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
        raise_for_kimss_error(response)

        def _gen() -> Generator[Dict[str, Any], None, None]:
            yield from self._client._iter_sse_json(response)

        return _gen()


class AgentRunUsage:
    """Read-only view of usage fields on an agent run ``res`` payload."""

    __slots__ = ("_raw",)

    def __init__(self, raw: Dict[str, Any]) -> None:
        self._raw = raw

    @property
    def total_credits(self) -> float:
        u = self._raw.get("usage")
        if isinstance(u, dict):
            tc = u.get("total_credits")
            if tc is not None:
                try:
                    return float(tc)
                except (TypeError, ValueError):
                    pass
        tc = self._raw.get("total_credits")
        if tc is not None:
            try:
                return float(tc)
            except (TypeError, ValueError):
                pass
        return 0.0


class AgentRunResult(dict):
    """``res`` payload from ``POST /v1/agents/run`` with convenience accessors.

    The response dict may still contain a ``thread_id`` key (Kimss wire name for
    the Foundry **conversation** id). Prefer :attr:`conversation_id` in new code.
    """

    __slots__ = ()

    @property
    def conversation_id(self) -> Optional[str]:
        """Foundry conversation id for the next turn (from ``thread_id`` or ``conversation_id`` in ``res``)."""
        for key in ("conversation_id", "thread_id"):
            v = self.get(key)
            if v is not None and str(v).strip():
                return str(v).strip()
        return None

    @property
    def text(self) -> str:
        for key in ("output", "response", "assistant_response"):
            v = self.get(key)
            if v is None:
                continue
            if isinstance(v, str):
                return v
            return str(v)
        return ""

    @property
    def usage(self) -> AgentRunUsage:
        return AgentRunUsage(self)

    @property
    def requires_action(self) -> bool:
        return bool(self.get("requires_action")) or str(self.get("status") or "") == "requires_action"

    @property
    def tool_calls(self) -> List[Dict[str, Any]]:
        raw = self.get("tool_calls")
        return list(raw) if isinstance(raw, list) else []

    @property
    def previous_response_id(self) -> Optional[str]:
        for key in ("previous_response_id", "response_id"):
            v = self.get(key)
            if v is not None and str(v).strip():
                return str(v).strip()
        return None


class UsageNamespace:
    """Self-reported BYO usage: POST /v1/usage/events (run API key scope).

    For streaming OpenAI-compatible calls, set ``stream_options={"include_usage": True}``
    so the final SSE chunk carries provider token counts — do not estimate.
    """

    def __init__(self, client: KimssClient) -> None:
        self._client = client

    def report(self, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Report a batch of usage events for previously registered external agents.

        Each event needs ``agent_id``, ``correlation_id``, ``prompt_tokens``,
        ``completion_tokens``. Optional: ``model``. Max 25 events per call.
        """
        if not isinstance(events, list) or not events:
            raise ValueError("usage.report requires a non-empty events list")
        r = self._client._post_json("/v1/usage/events", {"events": events}, timeout=60)
        raise_for_kimss_error(r)
        body = r.json()
        return body.get("res", body)


class DwNamespace:
    """Isolated Digital Worker Hermis orchestrator (``POST /v1/dw/hermis_chat``).

    Does not flip ``KIMSS_HERMIS_RUNTIME``. Customer Foundry chat stays on
    ``/v1/agents/run`` / ``/assistant_chat``.
    """

    def __init__(self, client: KimssClient) -> None:
        self._client = client

    def hermis_chat(
        self,
        *,
        agent_id: str,
        messages: Optional[List[Dict[str, Any]]] = None,
        prompt: Optional[str] = None,
        system: Optional[str] = None,
        thread_id: Optional[str] = None,
        max_tokens: Optional[int] = None,
        tenant_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        aid = (agent_id or "").strip()
        if not aid:
            raise ValueError("dw.hermis_chat requires agent_id")
        turns: List[Dict[str, Any]]
        if messages is not None:
            turns = list(messages)
        else:
            text = (prompt or "").strip()
            if not text:
                raise ValueError("dw.hermis_chat requires messages or a non-empty prompt")
            turns = [{"role": "user", "content": text}]
        payload: Dict[str, Any] = {"agent_id": aid, "messages": turns}
        if system is not None:
            payload["system"] = system
        if thread_id is not None and str(thread_id).strip():
            payload["thread_id"] = str(thread_id).strip()
        if max_tokens is not None:
            payload["max_tokens"] = int(max_tokens)
        if tenant_id is not None and str(tenant_id).strip():
            payload["tenant_id"] = str(tenant_id).strip()
        r = self._client._post_json("/v1/dw/hermis_chat", payload, timeout=180)
        raise_for_kimss_error(r)
        body = r.json()
        return body.get("res", body) if isinstance(body, dict) else body


class AgentsRunV1:
    """v1 agent management + orchestration.

    - ``create``   -> POST /v1/agents/create (Foundry-hosted; management scope).
    - ``register`` -> POST /v1/agents/register (customer-owned inventory; management scope).
    - ``run``      -> POST /v1/agents/run (hosted orchestration).
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
        raise_for_kimss_error(r)
        body = r.json()
        return body.get("res", body)

    def register(
        self,
        *,
        name: str,
        framework: Optional[str] = None,
        models: Optional[List[str]] = None,
        description: Optional[str] = None,
        owner: Optional[str] = None,
        purpose: Optional[str] = None,
        risk_tier: Optional[str] = None,
        endpoint_url: Optional[str] = None,
        external_ref: Optional[str] = None,
        tenant_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Register a customer-owned (external) agent in the Kimss inventory.

        Does not create a Foundry-hosted agent. Requires a **management** API key
        scope. Returns ``{"agent_id": "ext-...", "origin": "external", ...}``.
        """
        payload: Dict[str, Any] = {"name": (name or "").strip()}
        if not payload["name"]:
            raise ValueError("agents.register requires a non-empty name")
        if framework is not None and str(framework).strip():
            payload["framework"] = str(framework).strip()
        if models is not None:
            payload["models"] = [str(m).strip() for m in models if str(m or "").strip()]
        if description is not None:
            payload["description"] = description
        if owner is not None and str(owner).strip():
            payload["owner"] = str(owner).strip()
        if purpose is not None:
            payload["purpose"] = purpose
        if risk_tier is not None and str(risk_tier).strip():
            payload["risk_tier"] = str(risk_tier).strip()
        if endpoint_url is not None and str(endpoint_url).strip():
            payload["endpoint_url"] = str(endpoint_url).strip()
        if external_ref is not None and str(external_ref).strip():
            payload["external_ref"] = str(external_ref).strip()
        if tenant_id is not None and str(tenant_id).strip():
            payload["tenant_id"] = str(tenant_id).strip()
        r = self._client._post_json("/v1/agents/register", payload, timeout=60)
        raise_for_kimss_error(r)
        body = r.json()
        return body.get("res", body)

    def run(
        self,
        assistant_id: Optional[str] = None,
        message: Optional[str] = None,
        *,
        agent_id: Optional[str] = None,
        prompt: Optional[str] = None,
        tags: Optional[Any] = None,
        routing_preference: Optional[str] = None,
        stream: bool = False,
        conversation_id: Optional[str] = None,
        chat_type: str = "user_chat",
        tools: Optional[Dict[str, Any]] = None,
        max_tool_rounds: int = 16,
    ) -> Union[AgentRunResult, Dict[str, Any], Generator[Dict[str, Any], None, None]]:
        """Run an agent turn.

        When ``tools`` is a mapping of ``{name: callable}``, the SDK executes those
        functions locally whenever the API returns ``requires_action`` (client-side
        tool loop / Agentic RAG pattern).
        """
        aid = str(assistant_id or "").strip() or str(agent_id or "").strip()
        msg_src = message if message is not None else prompt
        usr_chat = "" if msg_src is None else str(msg_src)
        if not aid:
            raise ValueError("agents.run requires assistant_id or agent_id")
        if not usr_chat.strip() and not tools:
            raise ValueError("agents.run requires message or prompt")

        client_tools: Dict[str, Any] = {}
        if isinstance(tools, dict):
            client_tools = {str(k).strip(): v for k, v in tools.items() if str(k).strip() and callable(v)}

        if stream and client_tools:
            raise ValueError("agents.run client-side tools= is not supported with stream=True")

        payload: Dict[str, Any] = {
            "assistant_id": aid,
            "usr_chat": usr_chat or " ",
            "stream": stream,
            "chat_type": chat_type,
        }
        if conversation_id:
            payload["thread_id"] = str(conversation_id).strip()
        if tags:
            payload["tags"] = tags
        rp = str(routing_preference or "").strip()
        if rp:
            payload["routing_preference"] = rp
        if client_tools:
            payload["client_tool_names"] = list(client_tools.keys())

        if stream:
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
            raise_for_kimss_error(response)

            def _gen() -> Generator[Dict[str, Any], None, None]:
                yield from self._client._iter_sse_json(response)

            return _gen()

        def _post_once(body: Dict[str, Any]) -> AgentRunResult:
            r = self._client._post_json("/v1/agents/run", body, timeout=120)
            raise_for_kimss_error(r)
            raw = r.json().get("res", r.json())
            if isinstance(raw, dict):
                return AgentRunResult(raw)
            return AgentRunResult({"output": str(raw), "status": "completed"})

        result = _post_once(payload)
        rounds = 0
        while client_tools and result.requires_action and rounds < max(1, int(max_tool_rounds)):
            rounds += 1
            outputs: List[Dict[str, Any]] = []
            for call in result.tool_calls:
                name = str(call.get("name") or "").strip()
                call_id = str(call.get("call_id") or call.get("id") or "").strip()
                args_raw = call.get("arguments") or "{}"
                try:
                    args = json.loads(args_raw) if isinstance(args_raw, str) else (args_raw or {})
                    if not isinstance(args, dict):
                        args = {"_": args}
                except Exception:
                    args = {"_raw": args_raw}
                fn = client_tools.get(name)
                try:
                    if fn is None:
                        out = f"tool_not_provided:{name}"
                    else:
                        try:
                            out_val = fn(**args)
                        except TypeError:
                            out_val = fn(args)
                        if out_val is None:
                            out = ""
                        elif isinstance(out_val, (str, int, float, bool)):
                            out = str(out_val)
                        else:
                            out = json.dumps(out_val, ensure_ascii=False)
                except Exception as exc:  # noqa: BLE001
                    out = str(exc)[:8000]
                outputs.append({"type": "function_call_output", "call_id": call_id, "output": out})
            cont: Dict[str, Any] = {
                "assistant_id": aid,
                "usr_chat": " ",
                "stream": False,
                "chat_type": chat_type,
                "client_tool_names": list(client_tools.keys()),
                "tool_outputs": outputs,
                "previous_response_id": result.previous_response_id,
            }
            if result.conversation_id:
                cont["thread_id"] = result.conversation_id
            result = _post_once(cont)
        return result