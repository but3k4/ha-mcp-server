"""Tests for automation, script, and scene tools."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest

from ha_mcp.tools import automations
from tests.conftest import ToolCapture

_STATES: list[dict[str, Any]] = [
    {"entity_id": "automation.morning_lights", "state": "on", "attributes": {}},
    {"entity_id": "automation.goodnight", "state": "off", "attributes": {}},
    {"entity_id": "script.goodnight", "state": "off", "attributes": {}},
    {"entity_id": "scene.movie_time", "state": "scening", "attributes": {}},
    {"entity_id": "light.kitchen", "state": "on", "attributes": {}},
]


@pytest.fixture
def tools(mock_client: MagicMock) -> dict[str, Any]:
    """Register automation tools against a mock client and return the tool dict."""

    capture = ToolCapture()
    automations.register(capture, mock_client)  # type: ignore[arg-type]
    return capture.tools


async def test_list_automations_filters_domain(
    tools: dict[str, Any], mock_client: MagicMock
) -> None:
    """
    list_automations returns only entities whose entity_id starts with 'automation.'.
    """

    mock_client.get.return_value = _STATES
    result = await tools["list_automations"]()
    assert len(result) == 2
    assert all(e["entity_id"].startswith("automation.") for e in result)


async def test_list_automations_empty(
    tools: dict[str, Any], mock_client: MagicMock
) -> None:
    """
    list_automations returns an empty list when no automation entities are present.
    """

    mock_client.get.return_value = [{"entity_id": "light.kitchen", "state": "on"}]
    result = await tools["list_automations"]()
    assert result == []


async def test_trigger_automation(
    tools: dict[str, Any], mock_client: MagicMock
) -> None:
    """trigger_automation calls the automation/trigger service with the entity_id."""

    mock_client.post.return_value = []
    await tools["trigger_automation"]("automation.morning_lights")
    mock_client.post.assert_called_once_with(
        "/api/services/automation/trigger",
        {"entity_id": "automation.morning_lights"},
    )


async def test_enable_automation(tools: dict[str, Any], mock_client: MagicMock) -> None:
    """enable_automation calls the automation/turn_on service with the entity_id."""

    mock_client.post.return_value = []
    await tools["enable_automation"]("automation.goodnight")
    mock_client.post.assert_called_once_with(
        "/api/services/automation/turn_on",
        {"entity_id": "automation.goodnight"},
    )


async def test_disable_automation(
    tools: dict[str, Any], mock_client: MagicMock
) -> None:
    """disable_automation calls the automation/turn_off service with the entity_id."""

    mock_client.post.return_value = []
    await tools["disable_automation"]("automation.goodnight")
    mock_client.post.assert_called_once_with(
        "/api/services/automation/turn_off",
        {"entity_id": "automation.goodnight"},
    )


async def test_reload_automations_returns_count(
    tools: dict[str, Any], mock_client: MagicMock
) -> None:
    """
    reload_automations returns a string containing the count of reloaded automations.
    """

    mock_client.post.return_value = [{"entity_id": "automation.morning_lights"}]
    result = await tools["reload_automations"]()
    assert "1" in result
    mock_client.post.assert_called_once_with("/api/services/automation/reload")


async def test_reload_automations_empty_result(
    tools: dict[str, Any], mock_client: MagicMock
) -> None:
    """
    reload_automations returns a string containing '0' when the reload response
    is empty.
    """

    mock_client.post.return_value = []
    result = await tools["reload_automations"]()
    assert "0" in result


async def test_list_scripts_filters_domain(
    tools: dict[str, Any], mock_client: MagicMock
) -> None:
    """list_scripts returns only entities whose entity_id starts with 'script.'."""

    mock_client.get.return_value = _STATES
    result = await tools["list_scripts"]()
    assert len(result) == 1
    assert result[0]["entity_id"] == "script.goodnight"


async def test_run_script_without_variables(
    tools: dict[str, Any], mock_client: MagicMock
) -> None:
    """
    run_script calls script/turn_on with entity_id only when no variables are given.
    """

    mock_client.post.return_value = []
    await tools["run_script"]("script.goodnight")
    mock_client.post.assert_called_once_with(
        "/api/services/script/turn_on",
        {"entity_id": "script.goodnight"},
    )


async def test_run_script_with_variables(
    tools: dict[str, Any], mock_client: MagicMock
) -> None:
    """
    run_script includes a 'variables' key in the payload when variables are provided.
    """

    mock_client.post.return_value = []
    await tools["run_script"]("script.notify", variables={"message": "hello"})
    mock_client.post.assert_called_once_with(
        "/api/services/script/turn_on",
        {"entity_id": "script.notify", "variables": {"message": "hello"}},
    )


async def test_list_scenes_filters_domain(
    tools: dict[str, Any], mock_client: MagicMock
) -> None:
    """list_scenes returns only entities whose entity_id starts with 'scene.'."""

    mock_client.get.return_value = _STATES
    result = await tools["list_scenes"]()
    assert len(result) == 1
    assert result[0]["entity_id"] == "scene.movie_time"


async def test_activate_scene(tools: dict[str, Any], mock_client: MagicMock) -> None:
    """activate_scene calls the scene/turn_on service with the entity_id."""

    mock_client.post.return_value = []
    await tools["activate_scene"]("scene.movie_time")
    mock_client.post.assert_called_once_with(
        "/api/services/scene/turn_on",
        {"entity_id": "scene.movie_time"},
    )
