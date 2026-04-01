"""Tests for entity and service tools."""

from __future__ import annotations

import json
from typing import Any
from unittest.mock import MagicMock

import pytest

from ha_mcp.tools import entities
from tests.conftest import ToolCapture

_STATES: list[dict[str, Any]] = [
    {
        "entity_id": "light.kitchen",
        "state": "on",
        "attributes": {"friendly_name": "Kitchen Light", "brightness": 200},
    },
    {
        "entity_id": "switch.fan",
        "state": "off",
        "attributes": {"friendly_name": "Ceiling Fan"},
    },
    {
        "entity_id": "sensor.temperature",
        "state": "21.5",
        "attributes": {"friendly_name": "Temp Sensor", "unit_of_measurement": "°C"},
    },
]


@pytest.fixture
def tools(mock_client: MagicMock) -> dict[str, Any]:
    capture = ToolCapture()
    entities.register(capture, mock_client)  # type: ignore[arg-type]
    return capture.tools


# --- list_entities ---


async def test_list_entities_all(tools: dict[str, Any], mock_client: MagicMock) -> None:
    mock_client.get.return_value = _STATES
    result = await tools["list_entities"]()
    assert result == _STATES
    mock_client.get.assert_called_once_with("/api/states")


async def test_list_entities_domain_filter(tools: dict[str, Any], mock_client: MagicMock) -> None:
    mock_client.get.return_value = _STATES
    result = await tools["list_entities"](domain="light")
    assert len(result) == 1
    assert result[0]["entity_id"] == "light.kitchen"


async def test_list_entities_no_match(tools: dict[str, Any], mock_client: MagicMock) -> None:
    mock_client.get.return_value = _STATES
    result = await tools["list_entities"](domain="climate")
    assert result == []


# --- get_entity ---


async def test_get_entity(tools: dict[str, Any], mock_client: MagicMock) -> None:
    mock_client.get.return_value = _STATES[0]
    result = await tools["get_entity"]("light.kitchen")
    mock_client.get.assert_called_once_with("/api/states/light.kitchen")
    assert result["entity_id"] == "light.kitchen"


# --- set_entity_state ---


async def test_set_entity_state(tools: dict[str, Any], mock_client: MagicMock) -> None:
    expected = {"entity_id": "input_boolean.vacation_mode", "state": "on", "attributes": {}}
    mock_client.post.return_value = expected
    result = await tools["set_entity_state"]("input_boolean.vacation_mode", "on")
    mock_client.post.assert_called_once_with(
        "/api/states/input_boolean.vacation_mode",
        {"state": "on", "attributes": {}},
    )
    assert result == expected


async def test_set_entity_state_with_attributes(
    tools: dict[str, Any], mock_client: MagicMock
) -> None:
    mock_client.post.return_value = {}
    await tools["set_entity_state"]("input_text.label", "hello", attributes={"editable": True})
    mock_client.post.assert_called_once_with(
        "/api/states/input_text.label",
        {"state": "hello", "attributes": {"editable": True}},
    )


# --- call_service ---


async def test_call_service(tools: dict[str, Any], mock_client: MagicMock) -> None:
    mock_client.post.return_value = [_STATES[0]]
    result = await tools["call_service"]("light", "turn_on", {"entity_id": "light.kitchen"})
    mock_client.post.assert_called_once_with(
        "/api/services/light/turn_on",
        {"entity_id": "light.kitchen"},
    )
    assert result == [_STATES[0]]


async def test_call_service_no_data(tools: dict[str, Any], mock_client: MagicMock) -> None:
    mock_client.post.return_value = []
    await tools["call_service"]("homeassistant", "reload_all")
    mock_client.post.assert_called_once_with("/api/services/homeassistant/reload_all", {})


# --- search_entities ---


async def test_search_entities_by_entity_id(tools: dict[str, Any], mock_client: MagicMock) -> None:
    mock_client.get.return_value = _STATES
    result = await tools["search_entities"]("kitchen")
    assert len(result) == 1
    assert result[0]["entity_id"] == "light.kitchen"


async def test_search_entities_by_friendly_name(
    tools: dict[str, Any], mock_client: MagicMock
) -> None:
    mock_client.get.return_value = _STATES
    result = await tools["search_entities"]("ceiling fan")
    assert len(result) == 1
    assert result[0]["entity_id"] == "switch.fan"


async def test_search_entities_by_state(tools: dict[str, Any], mock_client: MagicMock) -> None:
    mock_client.get.return_value = _STATES
    result = await tools["search_entities"]("off")
    assert len(result) == 1
    assert result[0]["entity_id"] == "switch.fan"


async def test_search_entities_case_insensitive(
    tools: dict[str, Any], mock_client: MagicMock
) -> None:
    mock_client.get.return_value = _STATES
    result = await tools["search_entities"]("KITCHEN")
    assert len(result) == 1


async def test_search_entities_no_match(tools: dict[str, Any], mock_client: MagicMock) -> None:
    mock_client.get.return_value = _STATES
    result = await tools["search_entities"]("zzznomatch")
    assert result == []


# --- list_devices ---

_AREA_ENTRIES = [
    {"entity_id": "light.kitchen", "area_id": "kitchen", "area_name": "Kitchen"},
]


async def test_list_devices_merges_area_and_state(
    tools: dict[str, Any], mock_client: MagicMock
) -> None:
    mock_client.post.return_value = json.dumps(_AREA_ENTRIES)
    mock_client.get.return_value = _STATES

    result = await tools["list_devices"]()

    kitchen = next(d for d in result if d["entity_id"] == "light.kitchen")
    assert kitchen["area_id"] == "kitchen"
    assert kitchen["area_name"] == "Kitchen"
    assert kitchen["friendly_name"] == "Kitchen Light"

    fan = next(d for d in result if d["entity_id"] == "switch.fan")
    assert fan["area_id"] is None
    assert fan["area_name"] is None


async def test_list_devices_area_result_as_list(
    tools: dict[str, Any], mock_client: MagicMock
) -> None:
    """list_devices handles area_result already parsed as a list (not a JSON string)."""
    mock_client.post.return_value = _AREA_ENTRIES
    mock_client.get.return_value = _STATES

    result = await tools["list_devices"]()
    assert any(d["area_id"] == "kitchen" for d in result)


# --- list_entity_registry ---


async def test_list_entity_registry_only_area_entities(
    tools: dict[str, Any], mock_client: MagicMock
) -> None:
    mock_client.post.return_value = _AREA_ENTRIES
    mock_client.get.return_value = _STATES

    result = await tools["list_entity_registry"]()
    # Only entities with area assignments are returned
    assert len(result) == 1
    assert result[0]["entity_id"] == "light.kitchen"
    assert result[0]["friendly_name"] == "Kitchen Light"
    assert result[0]["area_name"] == "Kitchen"
