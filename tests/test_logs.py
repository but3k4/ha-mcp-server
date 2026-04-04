"""Tests for log-access tools."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest

from ha_mcp.tools import logs
from tests.conftest import ToolCapture


@pytest.fixture
def tools(mock_client: MagicMock) -> dict[str, Any]:
    """Register log tools against a mock client and return the tool dict."""

    capture = ToolCapture()
    logs.register(capture, mock_client)  # type: ignore[arg-type]
    return capture.tools


async def test_get_error_log(tools: dict[str, Any], mock_client: MagicMock) -> None:
    """get_error_log fetches the HA error log from /api/error_log as a plain string."""

    mock_client.get.return_value = "2024-01-01 ERROR something went wrong"
    result = await tools["get_error_log"]()
    assert "ERROR" in result
    mock_client.get.assert_called_once_with("/api/error_log")


async def test_get_supervisor_logs(
    tools: dict[str, Any], mock_client: MagicMock
) -> None:
    """get_supervisor_logs fetches Supervisor logs from the Hassio API."""

    mock_client.get.return_value = "supervisor log output"
    result = await tools["get_supervisor_logs"]()
    assert result == "supervisor log output"
    mock_client.get.assert_called_once_with("/api/hassio/supervisor/logs")


async def test_get_core_logs(tools: dict[str, Any], mock_client: MagicMock) -> None:
    """get_core_logs fetches HA core logs from the Hassio API."""

    mock_client.get.return_value = "core log output"
    result = await tools["get_core_logs"]()
    assert result == "core log output"
    mock_client.get.assert_called_once_with("/api/hassio/core/logs")


async def test_get_host_logs(tools: dict[str, Any], mock_client: MagicMock) -> None:
    """get_host_logs fetches host OS logs from the Hassio API."""

    mock_client.get.return_value = "host log output"
    result = await tools["get_host_logs"]()
    assert result == "host log output"
    mock_client.get.assert_called_once_with("/api/hassio/host/logs")


async def test_get_multicast_logs(
    tools: dict[str, Any], mock_client: MagicMock
) -> None:
    """get_multicast_logs fetches multicast add-on logs from the Hassio API."""

    mock_client.get.return_value = "multicast log output"
    result = await tools["get_multicast_logs"]()
    assert result == "multicast log output"
    mock_client.get.assert_called_once_with("/api/hassio/multicast/logs")
