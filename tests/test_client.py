"""Tests for HomeAssistantClient."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

from aioresponses import aioresponses
import pytest

from ha_mcp.client import HomeAssistantClient, HomeAssistantError

BASE_URL = "http://ha.local:8123"
TOKEN = "test-token"


async def test_get_returns_json() -> None:
    """GET request returns the parsed JSON body as a Python object."""

    with aioresponses() as m:
        m.get(f"{BASE_URL}/api/states", payload=[{"entity_id": "light.kitchen"}])
        async with HomeAssistantClient(BASE_URL, TOKEN) as client:
            result = await client.get("/api/states")
    assert result == [{"entity_id": "light.kitchen"}]


async def test_get_with_params() -> None:
    """GET request appends query parameters to the URL."""

    with aioresponses() as m:
        m.get(f"{BASE_URL}/api/history/period?filter_entity_id=light.a", payload=[])
        async with HomeAssistantClient(BASE_URL, TOKEN) as client:
            result = await client.get(
                "/api/history/period", params={"filter_entity_id": "light.a"}
            )
    assert result == []


async def test_get_non_json_returns_text() -> None:
    """Non-JSON responses (e.g. text/plain) are returned as a raw string."""

    with aioresponses() as m:
        m.get(
            f"{BASE_URL}/api/error_log",
            body="some log text",
            content_type="text/plain",
        )
        async with HomeAssistantClient(BASE_URL, TOKEN) as client:
            result = await client.get("/api/error_log")
    assert result == "some log text"


async def test_get_401_raises_error() -> None:
    """A 401 response raises HomeAssistantError with the status code in the message."""

    with aioresponses() as m:
        m.get(f"{BASE_URL}/api/states", status=401, body="Unauthorized")
        async with HomeAssistantClient(BASE_URL, TOKEN) as client:
            with pytest.raises(HomeAssistantError, match="401"):
                await client.get("/api/states")


async def test_get_404_raises_error() -> None:
    """A 404 response raises HomeAssistantError with the status code in the message."""

    with aioresponses() as m:
        m.get(f"{BASE_URL}/api/states/light.missing", status=404, body="Not found")
        async with HomeAssistantClient(BASE_URL, TOKEN) as client:
            with pytest.raises(HomeAssistantError, match="404"):
                await client.get("/api/states/light.missing")


async def test_post_returns_json() -> None:
    """POST request returns the parsed JSON response body."""

    with aioresponses() as m:
        m.post(
            f"{BASE_URL}/api/services/light/turn_on",
            payload=[{"entity_id": "light.kitchen", "state": "on"}],
        )
        async with HomeAssistantClient(BASE_URL, TOKEN) as client:
            result = await client.post(
                "/api/services/light/turn_on",
                {"entity_id": "light.kitchen"},
            )
    assert result[0]["state"] == "on"


async def test_post_sends_auth_header() -> None:
    """Bearer token must be included in every request."""

    with aioresponses() as m:
        m.post(f"{BASE_URL}/api/services/light/turn_on", payload=[])
        async with HomeAssistantClient(BASE_URL, TOKEN) as client:
            await client.post("/api/services/light/turn_on")

    # aioresponses captures the request. Verify it was sent to the right URL
    request = next(iter(m.requests.values()))[0]
    assert request.kwargs["headers"]["Authorization"] == f"Bearer {TOKEN}"


async def test_delete_returns_json() -> None:
    """DELETE request returns the parsed JSON response body."""

    with aioresponses() as m:
        m.delete(
            f"{BASE_URL}/api/lovelace/dashboards/old-dash",
            payload={"result": "ok"},
        )
        async with HomeAssistantClient(BASE_URL, TOKEN) as client:
            result = await client.delete("/api/lovelace/dashboards/old-dash")
    assert result == {"result": "ok"}


async def test_require_session_raises_outside_context() -> None:
    """_require_session raises RuntimeError when called outside an async context manager."""

    client = HomeAssistantClient(BASE_URL, TOKEN)
    with pytest.raises(RuntimeError, match="context manager"):
        client._require_session()


async def test_base_url_trailing_slash_stripped() -> None:
    """Trailing slash on base_url is stripped so request URLs are not double-slashed."""

    with aioresponses() as m:
        # If trailing slash were kept, the URL would be "http://ha.local:8123//api/states"
        m.get(f"{BASE_URL}/api/states", payload=[])
        async with HomeAssistantClient(f"{BASE_URL}/", TOKEN) as client:
            await client.get("/api/states")
    # passes without KeyError means the URL matched correctly


def _make_ws_mock(receive_side_effect: list[dict]) -> tuple[MagicMock, MagicMock]:
    """
    Return (session_mock, ws_mock) wired for use with patch("aiohttp.ClientSession").

    Args:
        receive_side_effect: Ordered list of dicts returned by ``receive_json``.

    Returns:
        A tuple of ``(session_mock, ws_mock)`` ready to be used with
        ``patch("aiohttp.ClientSession", return_value=session_mock)``.
    """
    ws = MagicMock()
    ws.receive_json = AsyncMock(side_effect=receive_side_effect)
    ws.send_json = AsyncMock()
    ws.__aenter__ = AsyncMock(return_value=ws)
    ws.__aexit__ = AsyncMock(return_value=None)

    session = MagicMock()
    session.ws_connect = MagicMock(return_value=ws)
    session.__aenter__ = AsyncMock(return_value=session)
    session.__aexit__ = AsyncMock(return_value=None)

    return session, ws


async def test_ws_command_returns_result() -> None:
    """ws_command completes the auth handshake and returns the result field."""

    session, ws = _make_ws_mock(
        [
            {"type": "auth_required"},
            {"type": "auth_ok"},
            {"id": 1, "type": "result", "success": True, "result": {"views": []}},
        ]
    )

    with patch("aiohttp.ClientSession", return_value=session):
        client = HomeAssistantClient(BASE_URL, TOKEN)
        result = await client.ws_command("lovelace/config")

    assert result == {"views": []}
    ws.send_json.assert_any_call({"type": "auth", "access_token": TOKEN})
    ws.send_json.assert_called_with({"id": 1, "type": "lovelace/config"})


async def test_ws_command_with_kwargs() -> None:
    """ws_command merges extra kwargs into the command message."""

    session, ws = _make_ws_mock(
        [
            {"type": "auth_required"},
            {"type": "auth_ok"},
            {"id": 1, "type": "result", "success": True, "result": None},
        ]
    )

    with patch("aiohttp.ClientSession", return_value=session):
        client = HomeAssistantClient(BASE_URL, TOKEN)
        await client.ws_command("lovelace/config", url_path="kiosk")

    ws.send_json.assert_called_with(
        {"id": 1, "type": "lovelace/config", "url_path": "kiosk"}
    )


async def test_ws_command_auth_failure_raises() -> None:
    """ws_command raises HomeAssistantError when HA rejects the auth token."""

    session, _ = _make_ws_mock(
        [
            {"type": "auth_required"},
            {"type": "auth_invalid", "message": "Invalid token"},
        ]
    )

    with patch("aiohttp.ClientSession", return_value=session):
        client = HomeAssistantClient(BASE_URL, TOKEN)
        with pytest.raises(HomeAssistantError, match="authentication failed"):
            await client.ws_command("lovelace/config")


async def test_ws_command_error_result_raises() -> None:
    """ws_command raises HomeAssistantError when the command returns success=false."""

    session, _ = _make_ws_mock(
        [
            {"type": "auth_required"},
            {"type": "auth_ok"},
            {
                "id": 1,
                "type": "result",
                "success": False,
                "error": {"code": "not_found", "message": "Dashboard not found"},
            },
        ]
    )

    with patch("aiohttp.ClientSession", return_value=session):
        client = HomeAssistantClient(BASE_URL, TOKEN)
        with pytest.raises(HomeAssistantError, match="not_found"):
            await client.ws_command("lovelace/config", url_path="missing")


async def test_ws_command_unexpected_first_message_raises() -> None:
    """ws_command raises HomeAssistantError if the first WS message is not auth_required."""

    session, _ = _make_ws_mock(
        [
            {"type": "something_unexpected"},
        ]
    )

    with patch("aiohttp.ClientSession", return_value=session):
        client = HomeAssistantClient(BASE_URL, TOKEN)
        with pytest.raises(HomeAssistantError, match="Expected auth_required"):
            await client.ws_command("lovelace/config")


async def test_ws_command_uses_wss_for_https() -> None:
    """ws_command derives wss:// when the base URL uses https://."""

    session, _ = _make_ws_mock(
        [
            {"type": "auth_required"},
            {"type": "auth_ok"},
            {"id": 1, "type": "result", "success": True, "result": None},
        ]
    )

    with patch("aiohttp.ClientSession", return_value=session):
        client = HomeAssistantClient("https://ha.local:8123", TOKEN)
        await client.ws_command("lovelace/config")

    session.ws_connect.assert_called_once_with("wss://ha.local:8123/api/websocket")
