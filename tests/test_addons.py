"""Tests for Supervisor add-on management tools."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from unittest.mock import MagicMock

import pytest

from ha_mcp.client import HomeAssistantError
from ha_mcp.tools import addons
from tests.conftest import ToolCapture

_ADDON_LIST: list[dict[str, Any]] = [
    {
        "slug": "core_mosquitto",
        "name": "Mosquitto broker",
        "state": "started",
        "version": "6.4.0",
        "version_latest": "6.4.0",
        "update_available": False,
    }
]

_ADDON_INFO: dict[str, Any] = {
    "slug": "core_mosquitto",
    "name": "Mosquitto broker",
    "state": "started",
    "version": "6.4.0",
    "options": {"logins": []},
}

_REPOSITORIES: list[dict[str, Any]] = [
    {
        "slug": "core",
        "name": "Official add-ons",
        "source": "core",
        "maintainer": "Home Assistant",
    }
]


@pytest.fixture
def tools() -> dict[str, Any]:
    """Register add-on tools and return the tool dict."""

    capture = ToolCapture()
    addons.register(capture)  # type: ignore[arg-type]
    return capture.tools


async def test_list_addons(
    tools: dict[str, Any], mock_ctx: MagicMock, mock_client: MagicMock
) -> None:
    """list_addons returns the add-on list from the nested data.addons key."""

    mock_client.get.return_value = {"data": {"addons": _ADDON_LIST}}
    result = await tools["list_addons"](ctx=mock_ctx)
    assert result == _ADDON_LIST
    mock_client.get.assert_called_once_with("/api/hassio/addons")


async def test_list_addons_empty(
    tools: dict[str, Any], mock_ctx: MagicMock, mock_client: MagicMock
) -> None:
    """list_addons returns an empty list when no add-ons are installed."""

    mock_client.get.return_value = {"data": {"addons": []}}
    result = await tools["list_addons"](ctx=mock_ctx)
    assert result == []


async def test_get_addon_info(
    tools: dict[str, Any], mock_ctx: MagicMock, mock_client: MagicMock
) -> None:
    """get_addon_info returns the add-on detail dict from the nested data key."""

    mock_client.get.return_value = {"data": _ADDON_INFO}
    result = await tools["get_addon_info"](ctx=mock_ctx, addon_slug="core_mosquitto")
    assert result == _ADDON_INFO
    mock_client.get.assert_called_once_with("/api/hassio/addons/core_mosquitto/info")


async def test_get_addon_info_fallback(
    tools: dict[str, Any], mock_ctx: MagicMock, mock_client: MagicMock
) -> None:
    """Falls back to the full response dict when no 'data' key present."""

    mock_client.get.return_value = _ADDON_INFO
    result = await tools["get_addon_info"](ctx=mock_ctx, addon_slug="core_mosquitto")
    assert result == _ADDON_INFO


async def test_install_addon(
    tools: dict[str, Any], mock_ctx: MagicMock, mock_client: MagicMock
) -> None:
    """install_addon POSTs to the install endpoint and returns the result string."""

    mock_client.post.return_value = {"result": "ok"}
    result = await tools["install_addon"](ctx=mock_ctx, addon_slug="core_ssh")
    assert result == "ok"
    mock_client.post.assert_called_once_with("/api/hassio/addons/core_ssh/install")


async def test_install_addon_fallback_str(
    tools: dict[str, Any], mock_ctx: MagicMock, mock_client: MagicMock
) -> None:
    """Falls back to str(response) when no 'result' key."""

    mock_client.post.return_value = {"status": "ok"}
    result = await tools["install_addon"](ctx=mock_ctx, addon_slug="core_ssh")
    assert "status" in result


async def test_uninstall_addon(
    tools: dict[str, Any], mock_ctx: MagicMock, mock_client: MagicMock
) -> None:
    """uninstall_addon POSTs to the uninstall endpoint and returns the result string."""

    mock_client.post.return_value = {"result": "ok"}
    result = await tools["uninstall_addon"](ctx=mock_ctx, addon_slug="core_ssh")
    assert result == "ok"
    mock_client.post.assert_called_once_with("/api/hassio/addons/core_ssh/uninstall")


async def test_update_addon(
    tools: dict[str, Any], mock_ctx: MagicMock, mock_client: MagicMock
) -> None:
    """update_addon POSTs to the update endpoint and returns the result string."""

    mock_client.post.return_value = {"result": "ok"}
    result = await tools["update_addon"](ctx=mock_ctx, addon_slug="core_mosquitto")
    assert result == "ok"
    mock_client.post.assert_called_once_with("/api/hassio/addons/core_mosquitto/update")


async def test_start_addon(
    tools: dict[str, Any], mock_ctx: MagicMock, mock_client: MagicMock
) -> None:
    """start_addon POSTs to the start endpoint and returns the result string."""

    mock_client.post.return_value = {"result": "ok"}
    result = await tools["start_addon"](ctx=mock_ctx, addon_slug="core_mosquitto")
    assert result == "ok"
    mock_client.post.assert_called_once_with("/api/hassio/addons/core_mosquitto/start")


async def test_stop_addon(
    tools: dict[str, Any], mock_ctx: MagicMock, mock_client: MagicMock
) -> None:
    """stop_addon POSTs to the stop endpoint and returns the result string."""

    mock_client.post.return_value = {"result": "ok"}
    result = await tools["stop_addon"](ctx=mock_ctx, addon_slug="core_mosquitto")
    assert result == "ok"
    mock_client.post.assert_called_once_with("/api/hassio/addons/core_mosquitto/stop")


async def test_restart_addon(
    tools: dict[str, Any], mock_ctx: MagicMock, mock_client: MagicMock
) -> None:
    """restart_addon POSTs to the restart endpoint and returns the result string."""

    mock_client.post.return_value = {"result": "ok"}
    result = await tools["restart_addon"](ctx=mock_ctx, addon_slug="core_mosquitto")
    assert result == "ok"
    mock_client.post.assert_called_once_with(
        "/api/hassio/addons/core_mosquitto/restart"
    )


async def test_get_addon_logs(
    tools: dict[str, Any], mock_ctx: MagicMock, mock_client: MagicMock
) -> None:
    """get_addon_logs returns the raw log text from the Hassio add-on logs endpoint."""

    mock_client.get.return_value = "addon log line 1\naddon log line 2"
    result = await tools["get_addon_logs"](ctx=mock_ctx, addon_slug="core_mosquitto")
    assert "addon log" in result
    mock_client.get.assert_called_once_with("/api/hassio/addons/core_mosquitto/logs")


async def test_set_addon_options(
    tools: dict[str, Any], mock_ctx: MagicMock, mock_client: MagicMock
) -> None:
    """
    set_addon_options POSTs options wrapped in an 'options' key and returns the
    result string.
    """

    mock_client.post.return_value = {"result": "ok"}
    result = await tools["set_addon_options"](
        ctx=mock_ctx,
        addon_slug="core_mosquitto",
        options={"logins": [{"username": "ha", "password": "secret"}]},
    )
    assert result == "ok"
    mock_client.post.assert_called_once_with(
        "/api/hassio/addons/core_mosquitto/options",
        {"options": {"logins": [{"username": "ha", "password": "secret"}]}},
    )


async def test_list_addon_repositories(
    tools: dict[str, Any], mock_ctx: MagicMock, mock_client: MagicMock
) -> None:
    """
    list_addon_repositories returns the repository list from the nested
    data.repositories key.
    """

    mock_client.get.return_value = {"data": {"repositories": _REPOSITORIES}}
    result = await tools["list_addon_repositories"](ctx=mock_ctx)
    assert result == _REPOSITORIES
    mock_client.get.assert_called_once_with("/api/hassio/store/repositories")


async def test_list_addon_repositories_empty(
    tools: dict[str, Any], mock_ctx: MagicMock, mock_client: MagicMock
) -> None:
    """list_addon_repositories returns an empty list when no repositories are configured."""

    mock_client.get.return_value = {"data": {"repositories": []}}
    result = await tools["list_addon_repositories"](ctx=mock_ctx)
    assert result == []


async def test_add_addon_repository(
    tools: dict[str, Any], mock_ctx: MagicMock, mock_client: MagicMock
) -> None:
    """add_addon_repository POSTs the repository URL and returns the result string."""

    mock_client.post.return_value = {"result": "ok"}
    result = await tools["add_addon_repository"](
        ctx=mock_ctx, repository_url="https://github.com/owner/repo"
    )
    assert result == "ok"
    mock_client.post.assert_called_once_with(
        "/api/hassio/store/repositories",
        {"repository": "https://github.com/owner/repo"},
    )


async def test_list_addons_error(
    tools: dict[str, Any], mock_ctx: MagicMock, mock_client: MagicMock
) -> None:
    """list_addons returns an error string when the API call fails."""

    mock_client.get.side_effect = HomeAssistantError("api failure")
    result = await tools["list_addons"](ctx=mock_ctx)
    assert isinstance(result, str)
    assert result.startswith("Error:")


async def test_get_addon_info_error(
    tools: dict[str, Any], mock_ctx: MagicMock, mock_client: MagicMock
) -> None:
    """get_addon_info returns an error string when the API call fails."""

    mock_client.get.side_effect = HomeAssistantError("api failure")
    result = await tools["get_addon_info"](ctx=mock_ctx, addon_slug="core_mosquitto")
    assert isinstance(result, str)
    assert result.startswith("Error:")


async def test_install_addon_error(
    tools: dict[str, Any], mock_ctx: MagicMock, mock_client: MagicMock
) -> None:
    """install_addon returns an error string when the API call fails."""

    mock_client.post.side_effect = HomeAssistantError("api failure")
    result = await tools["install_addon"](ctx=mock_ctx, addon_slug="core_ssh")
    assert isinstance(result, str)
    assert result.startswith("Error:")


async def test_uninstall_addon_error(
    tools: dict[str, Any], mock_ctx: MagicMock, mock_client: MagicMock
) -> None:
    """uninstall_addon returns an error string when the API call fails."""

    mock_client.post.side_effect = HomeAssistantError("api failure")
    result = await tools["uninstall_addon"](ctx=mock_ctx, addon_slug="core_ssh")
    assert isinstance(result, str)
    assert result.startswith("Error:")


async def test_update_addon_error(
    tools: dict[str, Any], mock_ctx: MagicMock, mock_client: MagicMock
) -> None:
    """update_addon returns an error string when the API call fails."""

    mock_client.post.side_effect = HomeAssistantError("api failure")
    result = await tools["update_addon"](ctx=mock_ctx, addon_slug="core_mosquitto")
    assert isinstance(result, str)
    assert result.startswith("Error:")


async def test_start_addon_error(
    tools: dict[str, Any], mock_ctx: MagicMock, mock_client: MagicMock
) -> None:
    """start_addon returns an error string when the API call fails."""

    mock_client.post.side_effect = HomeAssistantError("api failure")
    result = await tools["start_addon"](ctx=mock_ctx, addon_slug="core_mosquitto")
    assert isinstance(result, str)
    assert result.startswith("Error:")


async def test_stop_addon_error(
    tools: dict[str, Any], mock_ctx: MagicMock, mock_client: MagicMock
) -> None:
    """stop_addon returns an error string when the API call fails."""

    mock_client.post.side_effect = HomeAssistantError("api failure")
    result = await tools["stop_addon"](ctx=mock_ctx, addon_slug="core_mosquitto")
    assert isinstance(result, str)
    assert result.startswith("Error:")


async def test_restart_addon_error(
    tools: dict[str, Any], mock_ctx: MagicMock, mock_client: MagicMock
) -> None:
    """restart_addon returns an error string when the API call fails."""

    mock_client.post.side_effect = HomeAssistantError("api failure")
    result = await tools["restart_addon"](ctx=mock_ctx, addon_slug="core_mosquitto")
    assert isinstance(result, str)
    assert result.startswith("Error:")


async def test_get_addon_logs_error(
    tools: dict[str, Any], mock_ctx: MagicMock, mock_client: MagicMock
) -> None:
    """get_addon_logs returns an error string when the API call fails."""

    mock_client.get.side_effect = HomeAssistantError("api failure")
    result = await tools["get_addon_logs"](ctx=mock_ctx, addon_slug="core_mosquitto")
    assert isinstance(result, str)
    assert result.startswith("Error:")


async def test_set_addon_options_error(
    tools: dict[str, Any], mock_ctx: MagicMock, mock_client: MagicMock
) -> None:
    """set_addon_options returns an error string when the API call fails."""

    mock_client.post.side_effect = HomeAssistantError("api failure")
    result = await tools["set_addon_options"](
        ctx=mock_ctx, addon_slug="core_mosquitto", options={"logins": []}
    )
    assert isinstance(result, str)
    assert result.startswith("Error:")


async def test_list_addon_repositories_error(
    tools: dict[str, Any], mock_ctx: MagicMock, mock_client: MagicMock
) -> None:
    """list_addon_repositories returns an error string when the API call fails."""

    mock_client.get.side_effect = HomeAssistantError("api failure")
    result = await tools["list_addon_repositories"](ctx=mock_ctx)
    assert isinstance(result, str)
    assert result.startswith("Error:")


async def test_add_addon_repository_error(
    tools: dict[str, Any], mock_ctx: MagicMock, mock_client: MagicMock
) -> None:
    """add_addon_repository returns an error string when the API call fails."""

    mock_client.post.side_effect = HomeAssistantError("api failure")
    result = await tools["add_addon_repository"](
        ctx=mock_ctx, repository_url="https://github.com/owner/repo"
    )
    assert isinstance(result, str)
    assert result.startswith("Error:")
