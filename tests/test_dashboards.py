"""Tests for Lovelace dashboard tools."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from unittest.mock import MagicMock

import pytest

from ha_mcp.client import HomeAssistantError
from ha_mcp.tools import dashboards
from tests.conftest import ToolCapture

_DASHBOARDS: list[dict[str, Any]] = [
    {"url_path": "lovelace", "title": "Home", "mode": "storage"},
    {"url_path": "lovelace-mobile", "title": "Mobile", "mode": "storage"},
]

_CONFIG: dict[str, Any] = {
    "title": "Home",
    "views": [
        {
            "title": "Main",
            "cards": []
        }
    ]
}


@pytest.fixture
def tools() -> dict[str, Any]:
    """Register dashboard tools and return the tool dict."""

    capture = ToolCapture()
    dashboards.register(capture)  # type: ignore[arg-type]
    return capture.tools


async def test_list_dashboards(
    tools: dict[str, Any], mock_ctx: MagicMock, mock_client: MagicMock
) -> None:
    """list_dashboards calls lovelace/dashboards/list and returns the result."""

    mock_client.ws_command.return_value = _DASHBOARDS
    result = await tools["list_dashboards"](ctx=mock_ctx)
    assert len(result) == 2
    assert result[0]["url_path"] == "lovelace"
    mock_client.ws_command.assert_called_once_with("lovelace/dashboards/list")


async def test_get_dashboard_config_default(
    tools: dict[str, Any],
    mock_ctx: MagicMock,
    mock_client: MagicMock
) -> None:
    """
    get_dashboard_config fetches the default dashboard when url_path is None.
    """

    mock_client.ws_command.return_value = _CONFIG
    result = await tools["get_dashboard_config"](ctx=mock_ctx)
    assert "views" in result
    mock_client.ws_command.assert_called_once_with("lovelace/config")


async def test_get_dashboard_config_named(
    tools: dict[str, Any],
    mock_ctx: MagicMock,
    mock_client: MagicMock
) -> None:
    """get_dashboard_config passes url_path for non-default dashboards."""

    mock_client.ws_command.return_value = _CONFIG
    await tools["get_dashboard_config"](ctx=mock_ctx, url_path="kiosk")
    mock_client.ws_command.assert_called_once_with(
        "lovelace/config",
        url_path="kiosk"
    )


async def test_get_dashboard_config_default_url_path(
    tools: dict[str, Any],
    mock_ctx: MagicMock,
    mock_client: MagicMock
) -> None:
    """
    url_path='lovelace' is treated the same as None. No url_path kwarg is sent.
    """

    mock_client.ws_command.return_value = _CONFIG
    await tools["get_dashboard_config"](ctx=mock_ctx, url_path="lovelace")
    mock_client.ws_command.assert_called_once_with("lovelace/config")


async def test_create_dashboard_minimal(
    tools: dict[str, Any],
    mock_ctx: MagicMock,
    mock_client: MagicMock
) -> None:
    """
    create_dashboard sends default sidebar and admin flags when optional args
    are omitted.
    """

    mock_client.ws_command.return_value = {
        "url_path": "new-dash", "title": "New"
    }
    result = await tools["create_dashboard"](
        ctx=mock_ctx, url_path="new-dash", title="New"
    )
    mock_client.ws_command.assert_called_once_with(
        "lovelace/dashboards/create",
        url_path="new-dash",
        title="New",
        show_in_sidebar=True,
        require_admin=False,
    )
    assert result["url_path"] == "new-dash"


async def test_create_dashboard_with_icon(
    tools: dict[str, Any],
    mock_ctx: MagicMock, mock_client: MagicMock
) -> None:
    """
    create_dashboard includes icon and custom sidebar/admin flags when provided.
    """

    mock_client.ws_command.return_value = {}
    await tools["create_dashboard"](
        ctx=mock_ctx,
        url_path="admin-dash",
        title="Admin",
        icon="mdi:shield",
        show_in_sidebar=False,
        require_admin=True,
    )
    call_kwargs = mock_client.ws_command.call_args.kwargs
    assert call_kwargs["icon"] == "mdi:shield"
    assert call_kwargs["require_admin"] is True
    assert call_kwargs["show_in_sidebar"] is False


async def test_update_dashboard_config_default(
    tools: dict[str, Any],
    mock_ctx: MagicMock,
    mock_client: MagicMock
) -> None:
    """
    update_dashboard_config sends lovelace/config/save with config only when no
    url_path is given.
    """

    mock_client.ws_command.return_value = None
    result = await tools["update_dashboard_config"](
        ctx=mock_ctx,
        config=_CONFIG
    )
    mock_client.ws_command.assert_called_once_with(
        "lovelace/config/save",
        config=_CONFIG,
    )
    assert "saved" in result.lower()


async def test_update_dashboard_config_named(
    tools: dict[str, Any],
    mock_ctx: MagicMock, mock_client: MagicMock
) -> None:
    """update_dashboard_config includes url_path for named dashboards."""

    mock_client.ws_command.return_value = None
    await tools["update_dashboard_config"](
        ctx=mock_ctx, config=_CONFIG, url_path="kiosk"
    )
    mock_client.ws_command.assert_called_once_with(
        "lovelace/config/save",
        url_path="kiosk",
        config=_CONFIG,
    )


async def test_delete_dashboard(
    tools: dict[str, Any],
    mock_ctx: MagicMock,
    mock_client: MagicMock
) -> None:
    """
    delete_dashboard calls lovelace/dashboards/delete with dashboard_id and
    returns a confirmation string.
    """

    mock_client.ws_command.return_value = None
    result = await tools["delete_dashboard"](
        ctx=mock_ctx,
        dashboard_id="dashboard_old"
    )
    mock_client.ws_command.assert_called_once_with(
        "lovelace/dashboards/delete",
        dashboard_id="dashboard_old",
    )
    assert "dashboard_old" in result


async def test_update_dashboard(
    tools: dict[str, Any],
    mock_ctx: MagicMock,
    mock_client: MagicMock
) -> None:
    """
    update_dashboard calls lovelace/dashboards/update with only the provided
    fields and returns a confirmation string.
    """

    mock_client.ws_command.return_value = None
    result = await tools["update_dashboard"](
        ctx=mock_ctx, dashboard_id="dashboard_ios", title="Tablet"
    )
    mock_client.ws_command.assert_called_once_with(
        "lovelace/dashboards/update",
        dashboard_id="dashboard_ios",
        title="Tablet",
    )
    assert "dashboard_ios" in result


async def test_update_dashboard_multiple_fields(
    tools: dict[str, Any],
    mock_ctx: MagicMock,
    mock_client: MagicMock
) -> None:
    """update_dashboard passes only the non-None kwargs to ws_command."""

    mock_client.ws_command.return_value = None
    await tools["update_dashboard"](
        ctx=mock_ctx,
        dashboard_id="dashboard_ios",
        title="Tablet",
        icon="mdi:tablet",
        show_in_sidebar=True,
    )
    mock_client.ws_command.assert_called_once_with(
        "lovelace/dashboards/update",
        dashboard_id="dashboard_ios",
        title="Tablet",
        icon="mdi:tablet",
        show_in_sidebar=True,
    )


async def test_list_dashboards_error(
    tools: dict[str, Any],
    mock_ctx: MagicMock, mock_client: MagicMock
) -> None:
    """list_dashboards propagates HomeAssistantError on WebSocket failure."""

    mock_client.ws_command.side_effect = HomeAssistantError("ws failure")
    with pytest.raises(HomeAssistantError, match="ws failure"):
        await tools["list_dashboards"](ctx=mock_ctx)


async def test_get_dashboard_config_error(
    tools: dict[str, Any],
    mock_ctx: MagicMock,
    mock_client: MagicMock
) -> None:
    """get_dashboard_config propagates HomeAssistantError on WebSocket failure."""

    mock_client.ws_command.side_effect = HomeAssistantError("ws failure")
    with pytest.raises(HomeAssistantError, match="ws failure"):
        await tools["get_dashboard_config"](ctx=mock_ctx)


async def test_create_dashboard_error(
    tools: dict[str, Any],
    mock_ctx: MagicMock,
    mock_client: MagicMock
) -> None:
    """create_dashboard propagates HomeAssistantError on WebSocket failure."""

    mock_client.ws_command.side_effect = HomeAssistantError("ws failure")
    with pytest.raises(HomeAssistantError, match="ws failure"):
        await tools["create_dashboard"](
            ctx=mock_ctx, url_path="new-dash", title="New"
        )


async def test_update_dashboard_config_error(
    tools: dict[str, Any],
    mock_ctx: MagicMock,
    mock_client: MagicMock
) -> None:
    """update_dashboard_config propagates HomeAssistantError on WebSocket failure."""

    mock_client.ws_command.side_effect = HomeAssistantError("ws failure")
    with pytest.raises(HomeAssistantError, match="ws failure"):
        await tools["update_dashboard_config"](ctx=mock_ctx, config=_CONFIG)


async def test_update_dashboard_error(
    tools: dict[str, Any],
    mock_ctx: MagicMock, mock_client: MagicMock
) -> None:
    """update_dashboard propagates HomeAssistantError on WebSocket failure."""

    mock_client.ws_command.side_effect = HomeAssistantError("ws failure")
    with pytest.raises(HomeAssistantError, match="ws failure"):
        await tools["update_dashboard"](
            ctx=mock_ctx, dashboard_id="dashboard_ios", title="Tablet"
        )


async def test_delete_dashboard_error(
    tools: dict[str, Any],
    mock_ctx: MagicMock,
    mock_client: MagicMock
) -> None:
    """delete_dashboard propagates HomeAssistantError on WebSocket failure."""

    mock_client.ws_command.side_effect = HomeAssistantError("ws failure")
    with pytest.raises(HomeAssistantError, match="ws failure"):
        await tools["delete_dashboard"](
            ctx=mock_ctx,
            dashboard_id="dashboard_old"
        )
