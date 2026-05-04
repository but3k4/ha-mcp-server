"""Tests for server entry point: load_config and create_server."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

from mcp.server.fastmcp import FastMCP
import pytest

from ha_mcp.config import AppConfig, InstanceConfig, load_config
from ha_mcp.server import create_server, main


def test_load_config_missing_url(monkeypatch: pytest.MonkeyPatch) -> None:
    """load_config raises ValueError when no config file and HA_URL is not set."""

    monkeypatch.delenv("HA_CONFIG", raising=False)
    monkeypatch.delenv("HA_URL", raising=False)
    monkeypatch.delenv("HA_TOKEN", raising=False)
    with (
        patch("ha_mcp.config.load_dotenv"),
        patch.object(Path, "exists", return_value=False),
        pytest.raises(ValueError, match="HA_URL"),
    ):
        load_config()


def test_load_config_missing_token(monkeypatch: pytest.MonkeyPatch) -> None:
    """load_config raises ValueError when no config file and HA_TOKEN is not set."""

    monkeypatch.delenv("HA_CONFIG", raising=False)
    monkeypatch.setenv("HA_URL", "http://ha.local:8123")
    monkeypatch.delenv("HA_TOKEN", raising=False)
    with (
        patch("ha_mcp.config.load_dotenv"),
        patch.object(Path, "exists", return_value=False),
        pytest.raises(ValueError, match="HA_TOKEN"),
    ):
        load_config()


def test_load_config_env_vars(monkeypatch: pytest.MonkeyPatch) -> None:
    """load_config returns a single-instance AppConfig from HA_URL + HA_TOKEN."""

    monkeypatch.delenv("HA_CONFIG", raising=False)
    monkeypatch.setenv("HA_URL", "http://ha.local:8123")
    monkeypatch.setenv("HA_TOKEN", "test-token")
    with (
        patch("ha_mcp.config.load_dotenv"),
        patch.object(Path, "exists", return_value=False),
    ):
        config = load_config()

    assert isinstance(config, AppConfig)
    assert len(config.instances) == 1
    assert config.instances[0].name == "default"
    assert config.instances[0].url == "http://ha.local:8123"
    assert config.default == "default"


def test_load_config_from_yaml_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """load_config parses a YAML file when HA_CONFIG points to it."""

    yaml_file = tmp_path / "ha-mcp.yaml"
    yaml_file.write_text(
        "instances:\n"
        "  - name: home\n"
        "    url: http://home.local:8123\n"
        "    token: tok1\n"
        "  - name: office\n"
        "    url: http://office.local:8123\n"
        "    token: tok2\n"
        "default: office\n"
    )
    monkeypatch.setenv("HA_CONFIG", str(yaml_file))

    config = load_config()

    assert len(config.instances) == 2
    assert config.instances[0] == InstanceConfig(
        name="home", url="http://home.local:8123", token="tok1"
    )
    assert config.instances[1] == InstanceConfig(
        name="office", url="http://office.local:8123", token="tok2"
    )
    assert config.default == "office"


def test_load_config_from_json_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """load_config parses a JSON file when HA_CONFIG points to it."""

    json_file = tmp_path / "ha-mcp.json"
    json_file.write_text(
        json.dumps({
            "instances": [
                {"name": "home", "url": "http://home.local:8123", "token": "tok1"}
            ]
        })
    )
    monkeypatch.setenv("HA_CONFIG", str(json_file))

    config = load_config()

    assert config.instances[0].name == "home"
    assert config.default == "home"


def test_load_config_missing_file_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    """load_config raises FileNotFoundError when HA_CONFIG points to a missing file."""

    monkeypatch.setenv("HA_CONFIG", "/nonexistent/ha-mcp.yaml")
    with pytest.raises(FileNotFoundError, match="Config file not found"):
        load_config()


def test_load_config_empty_instances_raises(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """load_config raises ValueError when instances list is empty."""

    yaml_file = tmp_path / "ha-mcp.yaml"
    yaml_file.write_text("instances: []\n")
    monkeypatch.setenv("HA_CONFIG", str(yaml_file))

    with pytest.raises(ValueError, match="at least one entry"):
        load_config()


def test_create_server_returns_fastmcp(monkeypatch: pytest.MonkeyPatch) -> None:
    """create_server returns a FastMCP instance with all tools registered."""

    monkeypatch.setenv("HA_URL", "http://ha.local:8123")
    monkeypatch.setenv("HA_TOKEN", "test-token")
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


def test_main_rejects_invalid_transport(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    main() raises ValueError for a TRANSPORT value outside the allowed set
    rather than silently defaulting to stdio.
    """

    monkeypatch.setenv("TRANSPORT", "bogus")
    with pytest.raises(ValueError, match="Invalid TRANSPORT"):
        main()
