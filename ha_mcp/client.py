"""
Async HTTP client for the Home Assistant REST and Supervisor APIs.

Wraps aiohttp with auth headers and consistent error handling. Also provides
:meth: HomeAssistantClient.ws_command for one-shot WebSocket commands, which
is required for APIs (such as Lovelace dashboard management) that are not
available over REST in YAML-mode installations.
"""

from __future__ import annotations

import asyncio
import json
from typing import TYPE_CHECKING
from urllib.parse import urlparse, urlunparse

import aiohttp

if TYPE_CHECKING:
    from typing import Any

_WEBSOCKET_PATH = "/api/websocket"
_HTTP_ERROR_THRESHOLD = 400
_WS_CONNECT_TIMEOUT_SECONDS = 10
_WS_COMMAND_TIMEOUT_SECONDS = 30


class HomeAssistantError(Exception):
    """Raised when the Home Assistant API returns an error response."""


async def _parse_response(response: aiohttp.ClientResponse) -> Any:
    """
    Parse an aiohttp response, raising on error status codes.

    Args:
        response: The aiohttp response object.

    Returns:
        Parsed JSON body, or raw text if the body is not JSON.

    Raises:
        HomeAssistantError: If the HTTP status code indicates an error or the
                            body cannot be parsed as JSON despite advertising
                            application/json.
    """

    if response.status >= _HTTP_ERROR_THRESHOLD:
        body = await response.text()
        raise HomeAssistantError(
            f"HA API error {response.status} for {response.url}: {body}"
        )

    content_type = response.headers.get("Content-Type", "")

    if "application/json" in content_type:
        try:
            return await response.json()
        except json.JSONDecodeError as exc:
            raise HomeAssistantError(
                f"Invalid JSON response from {response.url}"
            ) from exc

    return await response.text()


class HomeAssistantClient:
    """
    Async client for the Home Assistant REST and Supervisor APIs.

    Args:
        base_url: Base URL of the Home Assistant instance, e.g.
                  http://homeassistant.local:8123.
        token: Long-lived access token generated in HA profile settings.

    Example:
        >>> async with HomeAssistantClient(
        ...     "http://localhost:8123", "mytoken"
        ... ) as client:
        ...     states = await client.get("/api/states")
    """

    def __init__(self, base_url: str, token: str) -> None:
        self._base_url = base_url.rstrip("/")
        self._token = token
        self._session: aiohttp.ClientSession | None = None

    async def __aenter__(self) -> HomeAssistantClient:
        """Open the underlying aiohttp session."""

        self._session = aiohttp.ClientSession(
            headers={
                "Authorization": f"Bearer {self._token}",
                "Content-Type": "application/json",
            },
            timeout=aiohttp.ClientTimeout(
                connect=_WS_CONNECT_TIMEOUT_SECONDS, total=None
            ),
        )

        return self

    async def __aexit__(self, *_: object) -> None:
        """Close the underlying aiohttp session."""

        if self._session:
            await self._session.close()
            self._session = None

    def _require_session(self) -> aiohttp.ClientSession:
        """
        Return the active session or raise if not initialised.

        Returns:
            The active aiohttp.ClientSession.

        Raises:
            RuntimeError: If the client is used outside of an async context
                          manager.
        """

        if self._session is None:
            raise RuntimeError(
                "HomeAssistantClient must be used as an async context manager."
            )

        return self._session

    async def get(self, path: str, params: dict[str, str] | None = None) -> Any:
        """
        Perform a GET request against the HA API.

        Args:
            path: API path, e.g. /api/states.
            params: Optional query parameters.

        Returns:
            Parsed JSON response body.

        Raises:
            HomeAssistantError: If the API returns a non-2xx status.
        """

        session = self._require_session()
        url = f"{self._base_url}{path}"

        async with session.get(url, params=params) as response:
            return await _parse_response(response)

    async def post(self, path: str, payload: dict[str, Any] | None = None) -> Any:
        """
        Perform a POST request against the HA API.

        Args:
            path: API path, e.g. /api/services/light/turn_on.
            payload: Optional JSON body.

        Returns:
            Parsed JSON response body.

        Raises:
            HomeAssistantError: If the API returns a non-2xx status.
        """

        session = self._require_session()
        url = f"{self._base_url}{path}"

        async with session.post(url, json=payload or {}) as response:
            return await _parse_response(response)

    async def ws_command(self, msg_type: str, **kwargs: Any) -> Any:
        """
        Send a single command over the HA WebSocket API and return its result.

        Reuses the existing session to open a WebSocket connection, completes
        the HA auth handshake, sends one command message, waits for the matching
        result message, then closes the WebSocket. Intermediate messages
        (events, progress updates) sharing the same id are skipped; only the
        terminal type="result" frame satisfies the wait. Separate timeouts cover
        the initial connection and the receive loop.

        Args:
            msg_type: HA WebSocket command type, e.g. lovelace/config or
                      lovelace/dashboards/list.
            **kwargs: Additional fields merged into the command message, e.g.
                      url_path="my-dash" or config={...}.

        Returns:
            The result field from the HA response message. May be None for
            commands that return no data (e.g. config/save).

        Raises:
            HomeAssistantError: If authentication is rejected, the command
                                returns success: false, the connection cannot
                                be established within the timeout, or no result
                                message arrives within the timeout window.
        """

        parsed = urlparse(self._base_url)
        scheme = "wss" if parsed.scheme == "https" else "ws"
        ws_url = urlunparse(
            parsed._replace(
                scheme=scheme, path=_WEBSOCKET_PATH, query="", fragment=""
            )
        )

        try:
            async with self._require_session().ws_connect(ws_url) as ws:
                first = await ws.receive_json()
                if first.get("type") != "auth_required":
                    raise HomeAssistantError(
                        f"Expected auth_required, got {first.get('type')!r}"
                    )

                await ws.send_json({"type": "auth", "access_token": self._token})
                auth_msg = await ws.receive_json()
                if auth_msg.get("type") != "auth_ok":
                    raise HomeAssistantError(
                        f"WebSocket authentication failed: {auth_msg}"
                    )

                cmd_id = 1
                await ws.send_json({"id": cmd_id, "type": msg_type, **kwargs})

                async def _await_result() -> dict[str, Any]:
                    while True:
                        msg = await ws.receive_json()
                        if msg.get("id") == cmd_id and msg.get("type") == "result":
                            return msg

                try:
                    msg = await asyncio.wait_for(
                        _await_result(), timeout=_WS_COMMAND_TIMEOUT_SECONDS
                    )
                except TimeoutError as exc:
                    raise HomeAssistantError(
                        f"WS command {msg_type!r} timed out after "
                        f"{_WS_COMMAND_TIMEOUT_SECONDS}s"
                    ) from exc

                if not msg.get("success"):
                    error = msg.get("error", {})
                    raise HomeAssistantError(
                        f"WS command {msg_type!r} failed: "
                        f"{error.get('code')} — {error.get('message')}"
                    )

                return msg.get("result")

        except TimeoutError as exc:
            raise HomeAssistantError(
                f"WS connection timed out after {_WS_CONNECT_TIMEOUT_SECONDS}s"
            ) from exc

    async def delete(self, path: str) -> Any:
        """
        Perform a DELETE request against the HA API.

        Args:
            path: API path.

        Returns:
            Parsed JSON response body.

        Raises:
            HomeAssistantError: If the API returns a non-2xx status.
        """

        session = self._require_session()
        url = f"{self._base_url}{path}"

        async with session.delete(url) as response:
            return await _parse_response(response)
