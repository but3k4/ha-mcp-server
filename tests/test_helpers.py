"""Tests for input helper and timer tools."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest

from ha_mcp.tools import helpers
from tests.conftest import ToolCapture

_STATES: list[dict[str, Any]] = [
    {"entity_id": "input_boolean.vacation_mode", "state": "off", "attributes": {}},
    {"entity_id": "input_number.target_temp", "state": "21.0", "attributes": {}},
    {
        "entity_id": "input_select.preset",
        "state": "Home",
        "attributes": {"options": ["Home", "Away"]},
    },
    {"entity_id": "input_text.label", "state": "hello", "attributes": {}},
    {"entity_id": "input_datetime.alarm", "state": "07:00:00", "attributes": {}},
    {"entity_id": "timer.cooking", "state": "idle", "attributes": {}},
    {"entity_id": "light.kitchen", "state": "on", "attributes": {}},
]


@pytest.fixture
def tools(mock_client: MagicMock) -> dict[str, Any]:
    capture = ToolCapture()
    helpers.register(capture, mock_client)  # type: ignore[arg-type]
    return capture.tools


# --- list_input_helpers ---


async def test_list_input_helpers_all(tools: dict[str, Any], mock_client: MagicMock) -> None:
    mock_client.get.return_value = _STATES
    result = await tools["list_input_helpers"]()
    entity_ids = [e["entity_id"] for e in result]
    assert "input_boolean.vacation_mode" in entity_ids
    assert "timer.cooking" in entity_ids
    assert "light.kitchen" not in entity_ids


async def test_list_input_helpers_domain_filter(
    tools: dict[str, Any], mock_client: MagicMock
) -> None:
    mock_client.get.return_value = _STATES
    result = await tools["list_input_helpers"](domain="input_boolean")
    assert len(result) == 1
    assert result[0]["entity_id"] == "input_boolean.vacation_mode"


async def test_list_input_helpers_timer_domain(
    tools: dict[str, Any], mock_client: MagicMock
) -> None:
    mock_client.get.return_value = _STATES
    result = await tools["list_input_helpers"](domain="timer")
    assert len(result) == 1
    assert result[0]["entity_id"] == "timer.cooking"


# --- set_input_boolean ---


async def test_set_input_boolean_on(tools: dict[str, Any], mock_client: MagicMock) -> None:
    mock_client.post.return_value = []
    await tools["set_input_boolean"]("input_boolean.vacation_mode", "on")
    mock_client.post.assert_called_once_with(
        "/api/services/input_boolean/turn_on",
        {"entity_id": "input_boolean.vacation_mode"},
    )


async def test_set_input_boolean_off(tools: dict[str, Any], mock_client: MagicMock) -> None:
    mock_client.post.return_value = []
    await tools["set_input_boolean"]("input_boolean.vacation_mode", "off")
    mock_client.post.assert_called_once_with(
        "/api/services/input_boolean/turn_off",
        {"entity_id": "input_boolean.vacation_mode"},
    )


async def test_set_input_boolean_invalid_state(
    tools: dict[str, Any], mock_client: MagicMock
) -> None:
    with pytest.raises(ValueError, match="'on' or 'off'"):
        await tools["set_input_boolean"]("input_boolean.x", "toggle")


# --- set_input_number ---


async def test_set_input_number(tools: dict[str, Any], mock_client: MagicMock) -> None:
    mock_client.post.return_value = []
    await tools["set_input_number"]("input_number.target_temp", 22.5)
    mock_client.post.assert_called_once_with(
        "/api/services/input_number/set_value",
        {"entity_id": "input_number.target_temp", "value": 22.5},
    )


# --- set_input_select ---


async def test_set_input_select(tools: dict[str, Any], mock_client: MagicMock) -> None:
    mock_client.post.return_value = []
    await tools["set_input_select"]("input_select.preset", "Away")
    mock_client.post.assert_called_once_with(
        "/api/services/input_select/select_option",
        {"entity_id": "input_select.preset", "option": "Away"},
    )


# --- set_input_text ---


async def test_set_input_text(tools: dict[str, Any], mock_client: MagicMock) -> None:
    mock_client.post.return_value = []
    await tools["set_input_text"]("input_text.label", "Welcome home!")
    mock_client.post.assert_called_once_with(
        "/api/services/input_text/set_value",
        {"entity_id": "input_text.label", "value": "Welcome home!"},
    )


# --- set_input_datetime ---


async def test_set_input_datetime_time_only(tools: dict[str, Any], mock_client: MagicMock) -> None:
    mock_client.post.return_value = []
    await tools["set_input_datetime"]("input_datetime.alarm", time="07:30:00")
    mock_client.post.assert_called_once_with(
        "/api/services/input_datetime/set_datetime",
        {"entity_id": "input_datetime.alarm", "time": "07:30:00"},
    )


async def test_set_input_datetime_full(tools: dict[str, Any], mock_client: MagicMock) -> None:
    mock_client.post.return_value = []
    await tools["set_input_datetime"](
        "input_datetime.alarm", date="2025-01-01", datetime_str="2025-01-01 08:00:00"
    )
    mock_client.post.assert_called_once_with(
        "/api/services/input_datetime/set_datetime",
        {
            "entity_id": "input_datetime.alarm",
            "date": "2025-01-01",
            "datetime": "2025-01-01 08:00:00",
        },
    )


# --- timers ---


async def test_start_timer_no_duration(tools: dict[str, Any], mock_client: MagicMock) -> None:
    mock_client.post.return_value = []
    await tools["start_timer"]("timer.cooking")
    mock_client.post.assert_called_once_with(
        "/api/services/timer/start",
        {"entity_id": "timer.cooking"},
    )


async def test_start_timer_with_duration(tools: dict[str, Any], mock_client: MagicMock) -> None:
    mock_client.post.return_value = []
    await tools["start_timer"]("timer.cooking", duration="00:05:00")
    mock_client.post.assert_called_once_with(
        "/api/services/timer/start",
        {"entity_id": "timer.cooking", "duration": "00:05:00"},
    )


async def test_pause_timer(tools: dict[str, Any], mock_client: MagicMock) -> None:
    mock_client.post.return_value = []
    await tools["pause_timer"]("timer.cooking")
    mock_client.post.assert_called_once_with(
        "/api/services/timer/pause", {"entity_id": "timer.cooking"}
    )


async def test_cancel_timer(tools: dict[str, Any], mock_client: MagicMock) -> None:
    mock_client.post.return_value = []
    await tools["cancel_timer"]("timer.cooking")
    mock_client.post.assert_called_once_with(
        "/api/services/timer/cancel", {"entity_id": "timer.cooking"}
    )
