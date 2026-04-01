"""
Async HTTP client for the Home Assistant REST and Supervisor APIs.

Wraps aiohttp with auth headers and consistent error handling.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import aiohttp

if TYPE_CHECKING:
    from typing import Any


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
        HomeAssistantError: If the HTTP status code indicates an error.
    """

    if response.status >= 400:
        body = await response.text()
        raise HomeAssistantError(f"HA API error {response.status} for {response.url}: {body}")

    content_type = response.headers.get("Content-Type", "")

    if "application/json" in content_type:
        return await response.json()

    return await response.text()


class HomeAssistantClient:
    """
    Async client for the Home Assistant REST and Supervisor APIs.

    Args:
        base_url: Base URL of the Home Assistant instance, e.g. ``http://homeassistant.local:8123``.
        token: Long-lived access token generated in HA profile settings.

    Example:
        >>> async with HomeAssistantClient("http://localhost:8123", "mytoken") as client:
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
            }
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
            RuntimeError: If the client is used outside of an async context manager.
        """

        if self._session is None:
            raise RuntimeError("HomeAssistantClient must be used as an async context manager.")

        return self._session

    async def get(self, path: str, params: dict[str, str] | None = None) -> Any:
        """
        Perform a GET request against the HA API.

        Args:
            path: API path, e.g. ``/api/states``.
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
        """Perform a POST request against the HA API.

        Args:
            path: API path, e.g. ``/api/services/light/turn_on``.
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
