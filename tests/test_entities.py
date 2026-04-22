"""Tests for entity and service tools."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from unittest.mock import MagicMock

import pytest

from ha_mcp.client import HomeAssistantError
from ha_mcp.tools import entities
from tests.conftest import ToolCapture

_STATES: list[dict[str, Any]] = [
    {
        "entity_id": "light.kitchen",
        "state": "on",
        "attributes": {
            "friendly_name": "Kitchen Light",
            "brightness": 200
        },
    },
    {
        "entity_id": "switch.fan",
        "state": "off",
        "attributes": {
            "friendly_name": "Ceiling Fan"
        },
    },
    {
        "entity_id": "sensor.temperature",
        "state": "21.5",
        "attributes": {
            "friendly_name": "Temp Sensor",
            "unit_of_measurement": "°C"
        },
    },
]


@pytest.fixture
def tools() -> dict[str, Any]:
    """Register entity tools and return the tool dict."""

    capture = ToolCapture()
    entities.register(capture)  # type: ignore[arg-type]
    return capture.tools


async def test_list_entities_all(
    tools: dict[str, Any],
    mock_ctx: MagicMock,
    mock_client: MagicMock
) -> None:
    """
    list_entities returns all states from /api/states when no domain filter is
    given.
    """

    mock_client.get.return_value = _STATES
    result = await tools["list_entities"](ctx=mock_ctx)
    assert result == _STATES
    mock_client.get.assert_called_once_with("/api/states")


async def test_list_entities_domain_filter(
    tools: dict[str, Any],
    mock_ctx: MagicMock,
    mock_client: MagicMock
) -> None:
    """
    list_entities filters results to only entities matching the given domain
    prefix.
    """

    mock_client.get.return_value = _STATES
    result = await tools["list_entities"](ctx=mock_ctx, domain="light")
    assert len(result) == 1
    assert result[0]["entity_id"] == "light.kitchen"


async def test_list_entities_no_match(
    tools: dict[str, Any],
    mock_ctx: MagicMock,
    mock_client: MagicMock
) -> None:
    """
    list_entities returns an empty list when no entity matches the given domain.
    """

    mock_client.get.return_value = _STATES
    result = await tools["list_entities"](ctx=mock_ctx, domain="climate")
    assert result == []


async def test_get_entity(
    tools: dict[str, Any],
    mock_ctx: MagicMock,
    mock_client: MagicMock
) -> None:
    """
    get_entity fetches a single entity state by entity_id from
    /api/states/{entity_id}.
    """

    mock_client.get.return_value = _STATES[0]
    result = await tools["get_entity"](
        ctx=mock_ctx,
        entity_id="light.kitchen"
    )
    mock_client.get.assert_called_once_with(
        "/api/states/light.kitchen"
    )
    assert result["entity_id"] == "light.kitchen"


async def test_set_entity_state(
    tools: dict[str, Any],
    mock_ctx: MagicMock,
    mock_client: MagicMock
) -> None:
    """
    set_entity_state POSTs state and empty attributes to
    /api/states/{entity_id}.
    """

    expected = {
        "entity_id": "input_boolean.vacation_mode",
        "state": "on",
        "attributes": {},
    }
    mock_client.post.return_value = expected
    result = await tools["set_entity_state"](
        ctx=mock_ctx,
        entity_id="input_boolean.vacation_mode",
        state="on"
    )
    mock_client.post.assert_called_once_with(
        "/api/states/input_boolean.vacation_mode",
        {"state": "on", "attributes": {}},
    )
    assert result == expected


async def test_set_entity_state_with_attributes(
    tools: dict[str, Any],
    mock_ctx: MagicMock,
    mock_client: MagicMock
) -> None:
    """set_entity_state merges custom attributes into the POST payload."""

    mock_client.post.return_value = {}
    await tools["set_entity_state"](
        ctx=mock_ctx,
        entity_id="input_text.label",
        state="hello",
        attributes={"editable": True},
    )
    mock_client.post.assert_called_once_with(
        "/api/states/input_text.label",
        {"state": "hello", "attributes": {"editable": True}},
    )


async def test_call_service(
    tools: dict[str, Any],
    mock_ctx: MagicMock,
    mock_client: MagicMock
) -> None:
    """
    call_service POSTs to /api/services/{domain}/{service} with service_data
    and returns affected states.
    """

    mock_client.post.return_value = [_STATES[0]]
    result = await tools["call_service"](
        ctx=mock_ctx,
        domain="light",
        service="turn_on",
        service_data={"entity_id": "light.kitchen"},
    )
    mock_client.post.assert_called_once_with(
        "/api/services/light/turn_on",
        {"entity_id": "light.kitchen"},
    )
    assert result == [_STATES[0]]


async def test_call_service_no_data(
    tools: dict[str, Any],
    mock_ctx: MagicMock,
    mock_client: MagicMock
) -> None:
    """
    call_service sends an empty dict as service_data when no service_data
    argument is given.
    """

    mock_client.post.return_value = []
    await tools["call_service"](
        ctx=mock_ctx, domain="homeassistant", service="reload_all"
    )
    mock_client.post.assert_called_once_with(
        "/api/services/homeassistant/reload_all", {}
    )


async def test_search_entities_by_entity_id(
    tools: dict[str, Any],
    mock_ctx: MagicMock,
    mock_client: MagicMock
) -> None:
    """search_entities matches the keyword against entity_id fields."""

    mock_client.get.return_value = _STATES
    result = await tools["search_entities"](ctx=mock_ctx, query="kitchen")
    assert len(result) == 1
    assert result[0]["entity_id"] == "light.kitchen"


async def test_search_entities_by_friendly_name(
    tools: dict[str, Any],
    mock_ctx: MagicMock,
    mock_client: MagicMock
) -> None:
    """search_entities matches the keyword against the friendly_name attribute."""

    mock_client.get.return_value = _STATES
    result = await tools["search_entities"](ctx=mock_ctx, query="ceiling fan")
    assert len(result) == 1
    assert result[0]["entity_id"] == "switch.fan"


async def test_search_entities_by_state(
    tools: dict[str, Any],
    mock_ctx: MagicMock,
    mock_client: MagicMock
) -> None:
    """search_entities matches the keyword against the state value."""

    mock_client.get.return_value = _STATES
    result = await tools["search_entities"](ctx=mock_ctx, query="off")
    assert len(result) == 1
    assert result[0]["entity_id"] == "switch.fan"


async def test_search_entities_case_insensitive(
    tools: dict[str, Any],
    mock_ctx: MagicMock,
    mock_client: MagicMock
) -> None:
    """search_entities matching is case-insensitive."""

    mock_client.get.return_value = _STATES
    result = await tools["search_entities"](ctx=mock_ctx, query="KITCHEN")
    assert len(result) == 1


async def test_search_entities_no_match(
    tools: dict[str, Any],
    mock_ctx: MagicMock,
    mock_client: MagicMock
) -> None:
    """search_entities returns an empty list when no entity matches the keyword."""

    mock_client.get.return_value = _STATES
    result = await tools["search_entities"](ctx=mock_ctx, query="zzznomatch")
    assert result == []


_AREA_ENTRIES: list[dict[str, Any]] = [
    {"entity_id": "light.kitchen", "area_id": "kitchen", "area_name": "Kitchen"},
]


async def test_list_devices_merges_area_and_state(
    tools: dict[str, Any],
    mock_ctx: MagicMock,
    mock_client: MagicMock
) -> None:
    """
    list_devices merges area info into each entity's state dict. Unassigned
    entities get None values.
    """

    mock_client.post.return_value = json.dumps(_AREA_ENTRIES)
    mock_client.get.return_value = _STATES

    result = await tools["list_devices"](ctx=mock_ctx)

    kitchen = next(d for d in result if d["entity_id"] == "light.kitchen")
    assert kitchen["area_id"] == "kitchen"
    assert kitchen["area_name"] == "Kitchen"
    assert kitchen["friendly_name"] == "Kitchen Light"

    fan = next(d for d in result if d["entity_id"] == "switch.fan")
    assert fan["area_id"] is None
    assert fan["area_name"] is None


async def test_list_devices_area_result_as_list(
    tools: dict[str, Any],
    mock_ctx: MagicMock,
    mock_client: MagicMock
) -> None:
    """
    list_devices handles area_result already parsed as a list (not a JSON
    string).
    """

    mock_client.post.return_value = _AREA_ENTRIES
    mock_client.get.return_value = _STATES

    result = await tools["list_devices"](ctx=mock_ctx)
    assert any(d["area_id"] == "kitchen" for d in result)


async def test_list_devices_malformed_template_json(
    tools: dict[str, Any],
    mock_ctx: MagicMock,
    mock_client: MagicMock
) -> None:
    """list_devices raises HomeAssistantError on malformed JSON from /api/template."""

    mock_client.post.return_value = "{not valid json"
    mock_client.get.return_value = _STATES

    with pytest.raises(HomeAssistantError, match="malformed JSON"):
        await tools["list_devices"](ctx=mock_ctx)


async def test_list_entity_registry_only_area_entities(
    tools: dict[str, Any],
    mock_ctx: MagicMock,
    mock_client: MagicMock
) -> None:
    """
    list_entity_registry returns entities with area info and friendly_name
    merged from state.
    """

    mock_client.post.return_value = _AREA_ENTRIES
    mock_client.get.return_value = _STATES

    result = await tools["list_entity_registry"](ctx=mock_ctx)
    assert len(result) == 1
    assert result[0]["entity_id"] == "light.kitchen"
    assert result[0]["friendly_name"] == "Kitchen Light"
    assert result[0]["area_name"] == "Kitchen"


async def test_list_services(
    tools: dict[str, Any],
    mock_ctx: MagicMock,
    mock_client: MagicMock
) -> None:
    """list_services returns the raw services list from /api/services."""

    services: list[dict[str, Any]] = [
        {
            "domain": "light", "services": {"turn_on": {}, "turn_off": {}}
        }
    ]
    mock_client.get.return_value = services
    result = await tools["list_services"](ctx=mock_ctx)
    assert result == services
    mock_client.get.assert_called_once_with("/api/services")


async def test_list_areas_json_string(
    tools: dict[str, Any],
    mock_ctx: MagicMock,
    mock_client: MagicMock
) -> None:
    """
    list_areas parses the response when the API returns areas as a JSON string.
    """

    areas = [{"area_id": "kitchen", "name": "Kitchen"}]
    mock_client.post.return_value = json.dumps(areas)
    result = await tools["list_areas"](ctx=mock_ctx)
    assert result == areas


async def test_list_areas_already_list(
    tools: dict[str, Any],
    mock_ctx: MagicMock,
    mock_client: MagicMock
) -> None:
    """
    list_areas passes through the response unchanged when it is already a list.
    """

    areas = [{"area_id": "kitchen", "name": "Kitchen"}]
    mock_client.post.return_value = areas
    result = await tools["list_areas"](ctx=mock_ctx)
    assert result == areas


async def test_list_areas_malformed_template_json(
    tools: dict[str, Any],
    mock_ctx: MagicMock,
    mock_client: MagicMock
) -> None:
    """list_areas raises HomeAssistantError on malformed JSON from /api/template."""

    mock_client.post.return_value = "not json at all"
    with pytest.raises(HomeAssistantError, match="malformed JSON"):
        await tools["list_areas"](ctx=mock_ctx)


async def test_get_entity_history_no_times(
    tools: dict[str, Any],
    mock_ctx: MagicMock,
    mock_client: MagicMock
) -> None:
    """
    get_entity_history fetches from /api/history/period with only the entity
    filter param.
    """

    history = [[{"entity_id": "sensor.temperature", "state": "21.5"}]]
    mock_client.get.return_value = history
    result = await tools["get_entity_history"](
        ctx=mock_ctx, entity_id="sensor.temperature"
    )
    assert result == history
    mock_client.get.assert_called_once_with(
        "/api/history/period",
        params={"filter_entity_id": "sensor.temperature"},
    )


async def test_get_entity_history_with_start(
    tools: dict[str, Any],
    mock_ctx: MagicMock,
    mock_client: MagicMock
) -> None:
    """get_entity_history includes start_time in the URL path when provided."""

    mock_client.get.return_value = [[]]
    await tools["get_entity_history"](
        ctx=mock_ctx,
        entity_id="sensor.temperature",
        start_time="2024-01-01T00:00:00",
    )
    mock_client.get.assert_called_once_with(
        "/api/history/period/2024-01-01T00:00:00",
        params={"filter_entity_id": "sensor.temperature"},
    )


async def test_get_entity_history_with_end(
    tools: dict[str, Any],
    mock_ctx: MagicMock,
    mock_client: MagicMock
) -> None:
    """
    get_entity_history passes end_time as a query param alongside start_time
    in the URL path.
    """

    mock_client.get.return_value = [[]]
    await tools["get_entity_history"](
        ctx=mock_ctx,
        entity_id="sensor.temperature",
        start_time="2024-01-01T00:00:00",
        end_time="2024-01-02T00:00:00",
    )
    mock_client.get.assert_called_once_with(
        "/api/history/period/2024-01-01T00:00:00",
        params={
            "filter_entity_id": "sensor.temperature",
            "end_time": "2024-01-02T00:00:00",
        },
    )


async def test_get_logbook_no_filters(
    tools: dict[str, Any],
    mock_ctx: MagicMock,
    mock_client: MagicMock
) -> None:
    """
    get_logbook fetches /api/logbook with no params when no arguments are
    provided.
    """

    entries = [{"name": "Kitchen Light", "message": "turned on"}]
    mock_client.get.return_value = entries
    result = await tools["get_logbook"](ctx=mock_ctx)
    assert result == entries
    mock_client.get.assert_called_once_with("/api/logbook", params=None)


async def test_get_logbook_with_entity(
    tools: dict[str, Any],
    mock_ctx: MagicMock,
    mock_client: MagicMock
) -> None:
    """get_logbook passes entity_id as the 'entity' query param."""

    mock_client.get.return_value = []
    await tools["get_logbook"](ctx=mock_ctx, entity_id="light.kitchen")
    mock_client.get.assert_called_once_with(
        "/api/logbook", params={"entity": "light.kitchen"}
    )


async def test_get_logbook_with_time_range(
    tools: dict[str, Any],
    mock_ctx: MagicMock,
    mock_client: MagicMock
) -> None:
    """
    get_logbook uses start_time in the URL path and end_time as a query param.
    """

    mock_client.get.return_value = []
    await tools["get_logbook"](
        ctx=mock_ctx,
        entity_id="light.kitchen",
        start_time="2024-01-01T00:00:00",
        end_time="2024-01-02T00:00:00",
    )
    mock_client.get.assert_called_once_with(
        "/api/logbook/2024-01-01T00:00:00",
        params={
            "entity": "light.kitchen",
            "end_time": "2024-01-02T00:00:00",
        },
    )


async def test_render_template(
    tools: dict[str, Any],
    mock_ctx: MagicMock,
    mock_client: MagicMock
) -> None:
    """
    render_template POSTs the template string to /api/template and returns
    the rendered result.
    """

    mock_client.post.return_value = "21.5"
    result = await tools["render_template"](
        ctx=mock_ctx, template="{{ states('sensor.temperature') }}"
    )
    assert result == "21.5"
    mock_client.post.assert_called_once_with(
        "/api/template",
        {"template": "{{ states('sensor.temperature') }}"},
    )


async def test_fire_event_no_data(
    tools: dict[str, Any],
    mock_ctx: MagicMock,
    mock_client: MagicMock
) -> None:
    """
    fire_event POSTs to /api/events/{event_type} with an empty payload when no
    event_data given.
    """

    mock_client.post.return_value = {"message": "Event fired."}
    result = await tools["fire_event"](
        ctx=mock_ctx,
        event_type="my_custom_event"
    )
    assert "message" in result
    mock_client.post.assert_called_once_with(
        "/api/events/my_custom_event", {}
    )


async def test_fire_event_with_data(
    tools: dict[str, Any],
    mock_ctx: MagicMock,
    mock_client: MagicMock
) -> None:
    """fire_event POSTs event_data as the request body when provided."""

    mock_client.post.return_value = {"message": "Event fired."}
    await tools["fire_event"](
        ctx=mock_ctx, event_type="my_event", event_data={"key": "value"}
    )
    mock_client.post.assert_called_once_with(
        "/api/events/my_event",
        {"key": "value"}
    )


async def test_list_entities_error(
    tools: dict[str, Any],
    mock_ctx: MagicMock,
    mock_client: MagicMock
) -> None:
    """list_entities propagates HomeAssistantError on API failure."""

    mock_client.get.side_effect = HomeAssistantError("api failure")
    with pytest.raises(HomeAssistantError, match="api failure"):
        await tools["list_entities"](ctx=mock_ctx)


async def test_get_entity_error(
    tools: dict[str, Any],
    mock_ctx: MagicMock,
    mock_client: MagicMock
) -> None:
    """get_entity propagates HomeAssistantError on API failure."""

    mock_client.get.side_effect = HomeAssistantError("api failure")
    with pytest.raises(HomeAssistantError, match="api failure"):
        await tools["get_entity"](
            ctx=mock_ctx,
            entity_id="light.kitchen"
        )


async def test_set_entity_state_error(
    tools: dict[str, Any],
    mock_ctx: MagicMock,
    mock_client: MagicMock
) -> None:
    """set_entity_state propagates HomeAssistantError on API failure."""

    mock_client.post.side_effect = HomeAssistantError("api failure")
    with pytest.raises(HomeAssistantError, match="api failure"):
        await tools["set_entity_state"](
            ctx=mock_ctx,
            entity_id="input_boolean.vacation_mode",
            state="on"
        )


async def test_call_service_error(
    tools: dict[str, Any],
    mock_ctx: MagicMock,
    mock_client: MagicMock
) -> None:
    """call_service propagates HomeAssistantError on API failure."""

    mock_client.post.side_effect = HomeAssistantError("api failure")
    with pytest.raises(HomeAssistantError, match="api failure"):
        await tools["call_service"](
            ctx=mock_ctx, domain="light", service="turn_on"
        )


async def test_search_entities_error(
    tools: dict[str, Any],
    mock_ctx: MagicMock,
    mock_client: MagicMock
) -> None:
    """search_entities propagates HomeAssistantError on API failure."""

    mock_client.get.side_effect = HomeAssistantError("api failure")
    with pytest.raises(HomeAssistantError, match="api failure"):
        await tools["search_entities"](ctx=mock_ctx, query="kitchen")


async def test_list_services_error(
    tools: dict[str, Any],
    mock_ctx: MagicMock,
    mock_client: MagicMock
) -> None:
    """list_services propagates HomeAssistantError on API failure."""

    mock_client.get.side_effect = HomeAssistantError("api failure")
    with pytest.raises(HomeAssistantError, match="api failure"):
        await tools["list_services"](ctx=mock_ctx)


async def test_list_areas_error(
    tools: dict[str, Any],
    mock_ctx: MagicMock,
    mock_client: MagicMock
) -> None:
    """list_areas propagates HomeAssistantError on API failure."""

    mock_client.post.side_effect = HomeAssistantError("api failure")
    with pytest.raises(HomeAssistantError, match="api failure"):
        await tools["list_areas"](ctx=mock_ctx)


async def test_list_devices_error(
    tools: dict[str, Any],
    mock_ctx: MagicMock,
    mock_client: MagicMock
) -> None:
    """list_devices propagates HomeAssistantError on API failure."""

    mock_client.post.side_effect = HomeAssistantError("api failure")
    with pytest.raises(HomeAssistantError, match="api failure"):
        await tools["list_devices"](ctx=mock_ctx)


async def test_list_entity_registry_error(
    tools: dict[str, Any],
    mock_ctx: MagicMock,
    mock_client: MagicMock
) -> None:
    """list_entity_registry propagates HomeAssistantError on API failure."""

    mock_client.post.side_effect = HomeAssistantError("api failure")
    with pytest.raises(HomeAssistantError, match="api failure"):
        await tools["list_entity_registry"](ctx=mock_ctx)


async def test_get_entity_history_error(
    tools: dict[str, Any],
    mock_ctx: MagicMock,
    mock_client: MagicMock
) -> None:
    """get_entity_history propagates HomeAssistantError on API failure."""

    mock_client.get.side_effect = HomeAssistantError("api failure")
    with pytest.raises(HomeAssistantError, match="api failure"):
        await tools["get_entity_history"](
            ctx=mock_ctx, entity_id="sensor.temperature"
        )


async def test_get_logbook_error(
    tools: dict[str, Any],
    mock_ctx: MagicMock,
    mock_client: MagicMock
) -> None:
    """get_logbook propagates HomeAssistantError on API failure."""

    mock_client.get.side_effect = HomeAssistantError("api failure")
    with pytest.raises(HomeAssistantError, match="api failure"):
        await tools["get_logbook"](ctx=mock_ctx)


async def test_render_template_error(
    tools: dict[str, Any],
    mock_ctx: MagicMock, mock_client: MagicMock
) -> None:
    """render_template propagates HomeAssistantError on API failure."""

    mock_client.post.side_effect = HomeAssistantError("api failure")
    with pytest.raises(HomeAssistantError, match="api failure"):
        await tools["render_template"](
            ctx=mock_ctx, template="{{ states('sensor.temperature') }}"
        )


async def test_fire_event_error(
    tools: dict[str, Any],
    mock_ctx: MagicMock,
    mock_client: MagicMock
) -> None:
    """fire_event propagates HomeAssistantError on API failure."""

    mock_client.post.side_effect = HomeAssistantError("api failure")
    with pytest.raises(HomeAssistantError, match="api failure"):
        await tools["fire_event"](
            ctx=mock_ctx,
            event_type="my_custom_event"
        )
