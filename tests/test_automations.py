"""Tests for automation, script, and scene tools."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from unittest.mock import MagicMock

import pytest

from ha_mcp.client import HomeAssistantError
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
def tools() -> dict[str, Any]:
    """Register automation tools and return the tool dict."""

    capture = ToolCapture()
    automations.register(capture)  # type: ignore[arg-type]
    return capture.tools


async def test_list_automations_filters_domain(
    tools: dict[str, Any],
    mock_ctx: MagicMock,
    mock_client: MagicMock
) -> None:
    """
    list_automations returns only entities whose entity_id starts with
    'automation.'.
    """

    mock_client.get.return_value = _STATES
    result = await tools["list_automations"](ctx=mock_ctx)
    assert len(result) == 2
    assert all(e["entity_id"].startswith("automation.") for e in result)


async def test_list_automations_empty(
    tools: dict[str, Any],
    mock_ctx: MagicMock,
    mock_client: MagicMock
) -> None:
    """
    list_automations returns an empty list when no automation entities are
    present.
    """

    mock_client.get.return_value = [
        {"entity_id": "light.kitchen", "state": "on"}
    ]
    result = await tools["list_automations"](ctx=mock_ctx)
    assert result == []


async def test_trigger_automation(
    tools: dict[str, Any],
    mock_ctx: MagicMock,
    mock_client: MagicMock
) -> None:
    """
    trigger_automation calls the automation/trigger service with the entity_id.
    """

    mock_client.post.return_value = []
    await tools["trigger_automation"](
        ctx=mock_ctx, entity_id="automation.morning_lights"
    )
    mock_client.post.assert_called_once_with(
        "/api/services/automation/trigger",
        {"entity_id": "automation.morning_lights"},
    )


async def test_enable_automation(
    tools: dict[str, Any],
    mock_ctx: MagicMock,
    mock_client: MagicMock
) -> None:
    """
    enable_automation calls the automation/turn_on service with the entity_id.
    """

    mock_client.post.return_value = []
    await tools["enable_automation"](
        ctx=mock_ctx,
        entity_id="automation.goodnight"
    )
    mock_client.post.assert_called_once_with(
        "/api/services/automation/turn_on",
        {"entity_id": "automation.goodnight"},
    )


async def test_disable_automation(
    tools: dict[str, Any],
    mock_ctx: MagicMock,
    mock_client: MagicMock
) -> None:
    """
    disable_automation calls the automation/turn_off service with the entity_id.
    """

    mock_client.post.return_value = []
    await tools["disable_automation"](
        ctx=mock_ctx,
        entity_id="automation.goodnight"
    )
    mock_client.post.assert_called_once_with(
        "/api/services/automation/turn_off",
        {"entity_id": "automation.goodnight"},
    )


async def test_reload_automations_returns_count(
    tools: dict[str, Any],
    mock_ctx: MagicMock,
    mock_client: MagicMock
) -> None:
    """
    reload_automations returns a string containing the count of reloaded
    automations.
    """

    mock_client.post.return_value = [{"entity_id": "automation.morning_lights"}]
    result = await tools["reload_automations"](ctx=mock_ctx)
    assert "1" in result
    mock_client.post.assert_called_once_with("/api/services/automation/reload")


async def test_reload_automations_empty_result(
    tools: dict[str, Any],
    mock_ctx: MagicMock,
    mock_client: MagicMock
) -> None:
    """
    reload_automations returns a string containing '0' when the reload response
    is empty.
    """

    mock_client.post.return_value = []
    result = await tools["reload_automations"](ctx=mock_ctx)
    assert "0" in result


async def test_list_scripts_filters_domain(
    tools: dict[str, Any],
    mock_ctx: MagicMock,
    mock_client: MagicMock
) -> None:
    """
    list_scripts returns only entities whose entity_id starts with 'script.'.
    """

    mock_client.get.return_value = _STATES
    result = await tools["list_scripts"](ctx=mock_ctx)
    assert len(result) == 1
    assert result[0]["entity_id"] == "script.goodnight"


async def test_run_script_without_variables(
    tools: dict[str, Any],
    mock_ctx: MagicMock,
    mock_client: MagicMock
) -> None:
    """
    run_script calls script/turn_on with entity_id only when no variables are
    given.
    """

    mock_client.post.return_value = []
    await tools["run_script"](ctx=mock_ctx, entity_id="script.goodnight")
    mock_client.post.assert_called_once_with(
        "/api/services/script/turn_on",
        {"entity_id": "script.goodnight"},
    )


async def test_run_script_with_variables(
    tools: dict[str, Any],
    mock_ctx: MagicMock,
    mock_client: MagicMock
) -> None:
    """
    run_script includes a 'variables' key in the payload when variables are
    provided.
    """

    mock_client.post.return_value = []
    await tools["run_script"](
        ctx=mock_ctx,
        entity_id="script.notify",
        variables={"message": "hello"},
    )
    mock_client.post.assert_called_once_with(
        "/api/services/script/turn_on",
        {"entity_id": "script.notify", "variables": {"message": "hello"}},
    )


async def test_list_scenes_filters_domain(
    tools: dict[str, Any],
    mock_ctx: MagicMock,
    mock_client: MagicMock
) -> None:
    """
    list_scenes returns only entities whose entity_id starts with 'scene.'.
    """

    mock_client.get.return_value = _STATES
    result = await tools["list_scenes"](ctx=mock_ctx)
    assert len(result) == 1
    assert result[0]["entity_id"] == "scene.movie_time"


async def test_activate_scene(
    tools: dict[str, Any],
    mock_ctx: MagicMock,
    mock_client: MagicMock
) -> None:
    """activate_scene calls the scene/turn_on service with the entity_id."""

    mock_client.post.return_value = []
    await tools["activate_scene"](ctx=mock_ctx, entity_id="scene.movie_time")
    mock_client.post.assert_called_once_with(
        "/api/services/scene/turn_on",
        {"entity_id": "scene.movie_time"},
    )


async def test_list_automations_error(
    tools: dict[str, Any],
    mock_ctx: MagicMock,
    mock_client: MagicMock
) -> None:
    """list_automations propagates HomeAssistantError when the API call fails."""

    mock_client.get.side_effect = HomeAssistantError("api failure")
    with pytest.raises(HomeAssistantError, match="api failure"):
        await tools["list_automations"](ctx=mock_ctx)


async def test_trigger_automation_error(
    tools: dict[str, Any],
    mock_ctx: MagicMock,
    mock_client: MagicMock
) -> None:
    """trigger_automation propagates HomeAssistantError when the API call fails."""

    mock_client.post.side_effect = HomeAssistantError("api failure")
    with pytest.raises(HomeAssistantError, match="api failure"):
        await tools["trigger_automation"](
            ctx=mock_ctx, entity_id="automation.morning_lights"
        )


async def test_enable_automation_error(
    tools: dict[str, Any],
    mock_ctx: MagicMock,
    mock_client: MagicMock
) -> None:
    """enable_automation propagates HomeAssistantError when the API call fails."""

    mock_client.post.side_effect = HomeAssistantError("api failure")
    with pytest.raises(HomeAssistantError, match="api failure"):
        await tools["enable_automation"](
            ctx=mock_ctx, entity_id="automation.goodnight"
        )


async def test_disable_automation_error(
    tools: dict[str, Any],
    mock_ctx: MagicMock,
    mock_client: MagicMock
) -> None:
    """disable_automation propagates HomeAssistantError when the API call fails."""

    mock_client.post.side_effect = HomeAssistantError("api failure")
    with pytest.raises(HomeAssistantError, match="api failure"):
        await tools["disable_automation"](
            ctx=mock_ctx, entity_id="automation.goodnight"
        )


async def test_reload_automations_error(
    tools: dict[str, Any],
    mock_ctx: MagicMock,
    mock_client: MagicMock
) -> None:
    """reload_automations propagates HomeAssistantError when the API call fails."""

    mock_client.post.side_effect = HomeAssistantError("api failure")
    with pytest.raises(HomeAssistantError, match="api failure"):
        await tools["reload_automations"](ctx=mock_ctx)


async def test_list_scripts_error(
    tools: dict[str, Any],
    mock_ctx: MagicMock,
    mock_client: MagicMock
) -> None:
    """list_scripts propagates HomeAssistantError when the API call fails."""

    mock_client.get.side_effect = HomeAssistantError("api failure")
    with pytest.raises(HomeAssistantError, match="api failure"):
        await tools["list_scripts"](ctx=mock_ctx)


async def test_run_script_error(
    tools: dict[str, Any],
    mock_ctx: MagicMock,
    mock_client: MagicMock
) -> None:
    """run_script propagates HomeAssistantError when the API call fails."""

    mock_client.post.side_effect = HomeAssistantError("api failure")
    with pytest.raises(HomeAssistantError, match="api failure"):
        await tools["run_script"](
            ctx=mock_ctx,
            entity_id="script.goodnight"
        )


async def test_list_scenes_error(
    tools: dict[str, Any],
    mock_ctx: MagicMock,
    mock_client: MagicMock
) -> None:
    """list_scenes propagates HomeAssistantError when the API call fails."""

    mock_client.get.side_effect = HomeAssistantError("api failure")
    with pytest.raises(HomeAssistantError, match="api failure"):
        await tools["list_scenes"](ctx=mock_ctx)


async def test_activate_scene_error(
    tools: dict[str, Any],
    mock_ctx: MagicMock,
    mock_client: MagicMock
) -> None:
    """activate_scene propagates HomeAssistantError when the API call fails."""

    mock_client.post.side_effect = HomeAssistantError("api failure")
    with pytest.raises(HomeAssistantError, match="api failure"):
        await tools["activate_scene"](
            ctx=mock_ctx,
            entity_id="scene.movie_time"
        )
