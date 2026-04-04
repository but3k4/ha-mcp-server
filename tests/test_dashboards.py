"""Tests for Lovelace dashboard tools."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest

from ha_mcp.tools import dashboards
from tests.conftest import ToolCapture

_DASHBOARDS: list[dict[str, Any]] = [
    {"url_path": "lovelace", "title": "Home", "mode": "storage"},
    {"url_path": "lovelace-mobile", "title": "Mobile", "mode": "storage"},
]

_CONFIG: dict[str, Any] = {"title": "Home", "views": [{"title": "Main", "cards": []}]}


@pytest.fixture
def tools(mock_client: MagicMock) -> dict[str, Any]:
    """Register dashboard tools against a mock client and return the tool dict."""

    capture = ToolCapture()
    dashboards.register(capture, mock_client)  # type: ignore[arg-type]
    return capture.tools


async def test_list_dashboards(tools: dict[str, Any], mock_client: MagicMock) -> None:
    """list_dashboards returns all dashboard entries from /api/lovelace/dashboards."""

    mock_client.get.return_value = _DASHBOARDS
    result = await tools["list_dashboards"]()
    assert len(result) == 2
    assert result[0]["url_path"] == "lovelace"
    mock_client.get.assert_called_once_with("/api/lovelace/dashboards")


async def test_get_dashboard_config_default(
    tools: dict[str, Any], mock_client: MagicMock
) -> None:
    """
    get_dashboard_config fetches the default dashboard config with no query params.
    """

    mock_client.get.return_value = _CONFIG
    result = await tools["get_dashboard_config"]()
    assert "views" in result
    mock_client.get.assert_called_once_with("/api/lovelace/config", params=None)


async def test_get_dashboard_config_named(
    tools: dict[str, Any], mock_client: MagicMock
) -> None:
    """
    get_dashboard_config passes url_path as a query param for non-default dashboards.
    """

    mock_client.get.return_value = _CONFIG
    await tools["get_dashboard_config"](url_path="lovelace-mobile")
    mock_client.get.assert_called_once_with(
        "/api/lovelace/config", params={"url_path": "lovelace-mobile"}
    )


async def test_get_dashboard_config_default_url_path(
    tools: dict[str, Any], mock_client: MagicMock
) -> None:
    """url_path='lovelace' is treated the same as None. No params sent."""

    mock_client.get.return_value = _CONFIG
    await tools["get_dashboard_config"](url_path="lovelace")
    mock_client.get.assert_called_once_with("/api/lovelace/config", params=None)


async def test_create_dashboard_minimal(
    tools: dict[str, Any], mock_client: MagicMock
) -> None:
    """
    create_dashboard sends default sidebar and admin flags when optional args
    are omitted.
    """

    mock_client.post.return_value = {"url_path": "new-dash", "title": "New"}
    result = await tools["create_dashboard"](url_path="new-dash", title="New")
    mock_client.post.assert_called_once_with(
        "/api/lovelace/dashboards",
        {
            "url_path": "new-dash",
            "title": "New",
            "show_in_sidebar": True,
            "require_admin": False,
        },
    )
    assert result["url_path"] == "new-dash"


async def test_create_dashboard_with_icon(
    tools: dict[str, Any], mock_client: MagicMock
) -> None:
    """create_dashboard includes icon and custom sidebar/admin flags when provided."""

    mock_client.post.return_value = {}
    await tools["create_dashboard"](
        url_path="admin-dash",
        title="Admin",
        icon="mdi:shield",
        show_in_sidebar=False,
        require_admin=True,
    )
    call_payload = mock_client.post.call_args[0][1]
    assert call_payload["icon"] == "mdi:shield"
    assert call_payload["require_admin"] is True
    assert call_payload["show_in_sidebar"] is False


async def test_update_dashboard_config_default(
    tools: dict[str, Any], mock_client: MagicMock
) -> None:
    """
    update_dashboard_config POSTs the config dict to /api/lovelace/config for
    the default dashboard.
    """

    mock_client.post.return_value = "ok"
    await tools["update_dashboard_config"](_CONFIG)
    mock_client.post.assert_called_once_with("/api/lovelace/config", _CONFIG)


async def test_update_dashboard_config_named(
    tools: dict[str, Any], mock_client: MagicMock
) -> None:
    """
    update_dashboard_config appends url_path as a query string for named dashboards.
    """

    mock_client.post.return_value = "ok"
    await tools["update_dashboard_config"](_CONFIG, url_path="lovelace-mobile")
    mock_client.post.assert_called_once_with(
        "/api/lovelace/config?url_path=lovelace-mobile", _CONFIG
    )


async def test_delete_dashboard(tools: dict[str, Any], mock_client: MagicMock) -> None:
    """
    delete_dashboard calls DELETE on /api/lovelace/dashboards/{url_path} and
    returns the response.
    """

    mock_client.delete.return_value = "ok"
    result = await tools["delete_dashboard"]("old-dash")
    assert result == "ok"
    mock_client.delete.assert_called_once_with("/api/lovelace/dashboards/old-dash")
