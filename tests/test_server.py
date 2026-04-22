"""Tests for server entry point: _load_client and create_server."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from mcp.server.fastmcp import FastMCP
import pytest

from ha_mcp.client import HomeAssistantClient
from ha_mcp.server import _load_client, create_server, main


def test_load_client_missing_url(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    """
    _load_client raises ValueError when the HA_URL environment variable is not
    set.
    """

    monkeypatch.delenv("HA_URL", raising=False)
    monkeypatch.delenv("HA_TOKEN", raising=False)
    with patch("ha_mcp.server.load_dotenv"), pytest.raises(ValueError, match="HA_URL"):
        _load_client()


def test_load_client_missing_token(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    """
    _load_client raises ValueError when the HA_TOKEN environment variable is
    not set.
    """

    monkeypatch.setenv("HA_URL", "http://ha.local:8123")
    monkeypatch.delenv("HA_TOKEN", raising=False)
    with (
        patch("ha_mcp.server.load_dotenv"),
        pytest.raises(ValueError, match="HA_TOKEN"),
    ):
        _load_client()


def test_load_client_returns_client(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    """
    _load_client returns a HomeAssistantClient when both env vars are present.
    """

    monkeypatch.setenv("HA_URL", "http://ha.local:8123")
    monkeypatch.setenv("HA_TOKEN", "test-token")
    with patch("ha_mcp.server.load_dotenv"):
        client = _load_client()
    assert isinstance(client, HomeAssistantClient)


def test_load_client_env_vars_take_precedence_over_dotenv(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    """
    When HA_URL and HA_TOKEN are already in the process environment,
    load_dotenv is not consulted. Env vars win over .env by design.
    """

    monkeypatch.setenv("HA_URL", "http://ha.local:8123")
    monkeypatch.setenv("HA_TOKEN", "from-env")
    with patch("ha_mcp.server.load_dotenv") as mock_load:
        _load_client()
    mock_load.assert_not_called()


def test_load_client_falls_back_to_dotenv(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    """
    When HA_URL or HA_TOKEN is missing, load_dotenv is invoked so a project
    .env file can supply the missing values.
    """

    monkeypatch.delenv("HA_URL", raising=False)
    monkeypatch.delenv("HA_TOKEN", raising=False)

    def populate_env(*_: object, **__: object) -> bool:
        monkeypatch.setenv("HA_URL", "http://ha.local:8123")
        monkeypatch.setenv("HA_TOKEN", "from-dotenv")
        return True

    with patch("ha_mcp.server.load_dotenv", side_effect=populate_env) as mock_load:
        client = _load_client()
    mock_load.assert_called_once()
    assert isinstance(client, HomeAssistantClient)


def test_create_server_returns_fastmcp(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    """
    create_server returns a FastMCP instance with all tools registered.
    """

    monkeypatch.setenv("HA_URL", "http://ha.local:8123")
    monkeypatch.setenv("HA_TOKEN", "test-token")
    with patch("ha_mcp.server.load_dotenv"):
        server = create_server()
    assert isinstance(server, FastMCP)
    tool_names = {t.name for t in server._tool_manager.list_tools()}
    assert len(tool_names) == 77


def test_main_calls_run_stdio(monkeypatch: pytest.MonkeyPatch) -> None:
    """main() defaults to stdio transport when TRANSPORT is not set."""

    monkeypatch.delenv("TRANSPORT", raising=False)
    mock_server = MagicMock()
    with patch("ha_mcp.server.create_server", return_value=mock_server):
        main()
    mock_server.run.assert_called_once_with(transport="stdio")


def test_main_calls_run_sse(monkeypatch: pytest.MonkeyPatch) -> None:
    """main() uses SSE transport and correct port when TRANSPORT=sse."""

    monkeypatch.setenv("TRANSPORT", "sse")
    monkeypatch.setenv("PORT", "9000")
    mock_server = MagicMock()
    with patch("ha_mcp.server.create_server", return_value=mock_server) as mock_create:
        main()
    mock_create.assert_called_once_with(port=9000)
    mock_server.run.assert_called_once_with(transport="sse")


def test_main_rejects_invalid_transport(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    """
    main() raises ValueError for a TRANSPORT value outside the allowed set
    rather than silently defaulting to stdio.
    """

    monkeypatch.setenv("TRANSPORT", "bogus")
    with pytest.raises(ValueError, match="Invalid TRANSPORT"):
        main()
