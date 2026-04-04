"""Tests for server entry point — _load_client and create_server."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from mcp.server.fastmcp import FastMCP

from ha_mcp.client import HomeAssistantClient
from ha_mcp.server import _load_client, create_server, main


def test_load_client_missing_url(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    _load_client raises ValueError when the HA_URL environment variable is not set.
    """

    monkeypatch.delenv("HA_URL", raising=False)
    monkeypatch.delenv("HA_TOKEN", raising=False)
    with patch("ha_mcp.server.load_dotenv"), pytest.raises(ValueError, match="HA_URL"):
        _load_client()


def test_load_client_missing_token(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    _load_client raises ValueError when the HA_TOKEN environment variable is not set.
    """

    monkeypatch.setenv("HA_URL", "http://ha.local:8123")
    monkeypatch.delenv("HA_TOKEN", raising=False)
    with (
        patch("ha_mcp.server.load_dotenv"),
        pytest.raises(ValueError, match="HA_TOKEN"),
    ):
        _load_client()


def test_load_client_returns_client(monkeypatch: pytest.MonkeyPatch) -> None:
    """_load_client returns a HomeAssistantClient when both env vars are present."""

    monkeypatch.setenv("HA_URL", "http://ha.local:8123")
    monkeypatch.setenv("HA_TOKEN", "test-token")
    with patch("ha_mcp.server.load_dotenv"):
        client = _load_client()
    assert isinstance(client, HomeAssistantClient)


def test_create_server_returns_fastmcp(monkeypatch: pytest.MonkeyPatch) -> None:
    """create_server returns a FastMCP instance with all tools registered."""

    monkeypatch.setenv("HA_URL", "http://ha.local:8123")
    monkeypatch.setenv("HA_TOKEN", "test-token")
    with patch("ha_mcp.server.load_dotenv"):
        server = create_server()
    assert isinstance(server, FastMCP)


def test_main_calls_run(monkeypatch: pytest.MonkeyPatch) -> None:
    """main() creates the server and calls run with the stdio transport."""

    mock_server = MagicMock()
    with patch("ha_mcp.server.create_server", return_value=mock_server):
        main()
    mock_server.run.assert_called_once_with(transport="stdio")
