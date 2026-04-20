"""Tests for log-access tools."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from unittest.mock import MagicMock

import pytest

from ha_mcp.client import HomeAssistantError
from ha_mcp.tools import logs
from tests.conftest import ToolCapture


@pytest.fixture
def tools() -> dict[str, Any]:
    """Register log tools and return the tool dict."""

    capture = ToolCapture()
    logs.register(capture)  # type: ignore[arg-type]
    return capture.tools


async def test_get_error_log(
    tools: dict[str, Any],
    mock_ctx: MagicMock,
    mock_client: MagicMock
) -> None:
    """
    get_error_log fetches the HA error log from /api/error_log as a plain string.
    """

    mock_client.get.return_value = "2024-01-01 ERROR something went wrong"
    result = await tools["get_error_log"](ctx=mock_ctx)
    assert "ERROR" in result
    mock_client.get.assert_called_once_with("/api/error_log")


async def test_get_supervisor_logs(
    tools: dict[str, Any],
    mock_ctx: MagicMock,
    mock_client: MagicMock
) -> None:
    """get_supervisor_logs fetches Supervisor logs from the Hassio API."""

    mock_client.get.return_value = "supervisor log output"
    result = await tools["get_supervisor_logs"](ctx=mock_ctx)
    assert result == "supervisor log output"
    mock_client.get.assert_called_once_with("/api/hassio/supervisor/logs")


async def test_get_core_logs(
    tools: dict[str, Any],
    mock_ctx: MagicMock,
    mock_client: MagicMock
) -> None:
    """get_core_logs fetches HA core logs from the Hassio API."""

    mock_client.get.return_value = "core log output"
    result = await tools["get_core_logs"](ctx=mock_ctx)
    assert result == "core log output"
    mock_client.get.assert_called_once_with("/api/hassio/core/logs")


async def test_get_host_logs(
    tools: dict[str, Any],
    mock_ctx: MagicMock,
    mock_client: MagicMock
) -> None:
    """get_host_logs fetches host OS logs from the Hassio API."""

    mock_client.get.return_value = "host log output"
    result = await tools["get_host_logs"](ctx=mock_ctx)
    assert result == "host log output"
    mock_client.get.assert_called_once_with("/api/hassio/host/logs")


async def test_get_multicast_logs(
    tools: dict[str, Any],
    mock_ctx: MagicMock,
    mock_client: MagicMock
) -> None:
    """get_multicast_logs fetches multicast add-on logs from the Hassio API."""

    mock_client.get.return_value = "multicast log output"
    result = await tools["get_multicast_logs"](ctx=mock_ctx)
    assert result == "multicast log output"
    mock_client.get.assert_called_once_with("/api/hassio/multicast/logs")


async def test_get_error_log_error(
    tools: dict[str, Any],
    mock_ctx: MagicMock,
    mock_client: MagicMock
) -> None:
    """get_error_log returns an error string when the API call fails."""

    mock_client.get.side_effect = HomeAssistantError("api failure")
    result = await tools["get_error_log"](ctx=mock_ctx)
    assert isinstance(result, str)
    assert result.startswith("Error:")


async def test_get_supervisor_logs_error(
    tools: dict[str, Any],
    mock_ctx: MagicMock,
    mock_client: MagicMock
) -> None:
    """get_supervisor_logs returns an error string when the API call fails."""

    mock_client.get.side_effect = HomeAssistantError("api failure")
    result = await tools["get_supervisor_logs"](ctx=mock_ctx)
    assert isinstance(result, str)
    assert result.startswith("Error:")


async def test_get_core_logs_error(
    tools: dict[str, Any],
    mock_ctx: MagicMock,
    mock_client: MagicMock
) -> None:
    """get_core_logs returns an error string when the API call fails."""

    mock_client.get.side_effect = HomeAssistantError("api failure")
    result = await tools["get_core_logs"](ctx=mock_ctx)
    assert isinstance(result, str)
    assert result.startswith("Error:")


async def test_get_host_logs_error(
    tools: dict[str, Any],
    mock_ctx: MagicMock,
    mock_client: MagicMock
) -> None:
    """get_host_logs returns an error string when the API call fails."""

    mock_client.get.side_effect = HomeAssistantError("api failure")
    result = await tools["get_host_logs"](ctx=mock_ctx)
    assert isinstance(result, str)
    assert result.startswith("Error:")


async def test_get_multicast_logs_error(
    tools: dict[str, Any],
    mock_ctx: MagicMock,
    mock_client: MagicMock
) -> None:
    """get_multicast_logs returns an error string when the API call fails."""

    mock_client.get.side_effect = HomeAssistantError("api failure")
    result = await tools["get_multicast_logs"](ctx=mock_ctx)
    assert isinstance(result, str)
    assert result.startswith("Error:")
