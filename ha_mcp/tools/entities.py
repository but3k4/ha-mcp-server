"""
MCP tools for Home Assistant entity and service management.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

    from ha_mcp.client import HomeAssistantClient

# Jinja2 template that returns every entity→area mapping as a JSON list.
# Used by both list_devices and list_entity_registry.
_AREA_ENTITIES_TEMPLATE = (
    "{%- set ns = namespace(entities=[]) -%}"
    "{%- for area_id in areas() -%}"
    "{%- for entity_id in area_entities(area_id) -%}"
    "{%- set ns.entities = ns.entities + [{"
    "'entity_id': entity_id,"
    "'area_id': area_id,"
    "'area_name': area_name(area_id)"
    "}] -%}"
    "{%- endfor -%}"
    "{%- endfor -%}"
    "{{ ns.entities | tojson }}"
)


def register(mcp: FastMCP, client: HomeAssistantClient) -> None:
    """
    Register all entity and service tools on the MCP server.

    Args:
        mcp: The FastMCP server instance to register tools on.
        client: The authenticated Home Assistant client.
    """

    @mcp.tool()
    async def list_entities(domain: str | None = None) -> list[dict[str, Any]]:
        """
        List all Home Assistant entities, optionally filtered by domain.

        Returns raw state objects from the HA state machine. Each object includes
        the full ``attributes`` dict, which may contain ``friendly_name``, unit of
        measurement, device class, and other domain-specific metadata. When
        ``domain`` is provided only entities whose ``entity_id`` starts with
        ``<domain>.`` are returned.

        Args:
            domain: Optional domain filter, e.g. ``light``, ``switch``, ``sensor``.

        Returns:
            A list of entity state objects with ``entity_id``, ``state``,
            and ``attributes``.
        """

        async with client:
            states: list[dict[str, Any]] = await client.get("/api/states")

        if domain is None:
            return states

        return [s for s in states if s["entity_id"].startswith(f"{domain}.")]

    @mcp.tool()
    async def get_entity(entity_id: str) -> dict[str, Any]:
        """
        Get the current state and attributes of a single entity.

        Fetches the live state directly from the HA state machine. Raises an
        HTTP error if the entity does not exist.

        Args:
            entity_id: Full entity ID, e.g. ``light.living_room``.

        Returns:
            Entity state object with ``entity_id``, ``state``,
            ``attributes``, and timestamps.
        """

        async with client:
            return await client.get(f"/api/states/{entity_id}")

    @mcp.tool()
    async def set_entity_state(
        entity_id: str,
        state: str,
        attributes: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Directly set the state and attributes of an entity in the HA state machine.

        This is a low-level write to the state machine and does **not** send a
        command to the underlying device. For physical devices (lights, switches,
        thermostats, etc.) use ``call_service`` instead. For input helpers prefer
        the dedicated ``set_input_boolean``, ``set_input_number``, and related
        tools over this one. This tool is primarily useful for writing arbitrary
        state to virtual entities that have no dedicated service.

        Args:
            entity_id: Full entity ID, e.g. ``input_boolean.vacation_mode``.
            state: New state string, e.g. ``on``, ``off``, ``home``.
            attributes: Optional dictionary of attributes to set alongside the state.

        Returns:
            The updated entity state object.
        """

        async with client:
            return await client.post(
                f"/api/states/{entity_id}",
                {"state": state, "attributes": attributes or {}},
            )

    @mcp.tool()
    async def call_service(
        domain: str,
        service: str,
        service_data: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Call a Home Assistant service. This is the primary way to control
        physical devices.

        Services are the correct mechanism for turning devices on/off, adjusting
        brightness, setting thermostat temperatures, running scripts, triggering
        automations, and so on. Use ``list_services`` to discover available
        domain/service combinations and their accepted parameters.

        Args:
            domain: Service domain, e.g. ``light``, ``switch``, ``climate``, ``script``.
            service: Service name, e.g. ``turn_on``, ``turn_off``, ``toggle``.
            service_data: Optional data payload,
                e.g. ``{"entity_id": "light.kitchen", "brightness": 200}``.

        Returns:
            List of entity states affected by the service call.
        """

        async with client:
            return await client.post(
                f"/api/services/{domain}/{service}",
                service_data or {},
            )

    @mcp.tool()
    async def search_entities(query: str) -> list[dict[str, Any]]:
        """
        Search for entities by matching a query string against entity ID,
        friendly name, and state.

        The match is case-insensitive and checks all three fields. An entity is
        included if the query appears in any one of them. Entities that have no
        ``friendly_name`` attribute are still searchable via their ``entity_id``
        and ``state``.

        Args:
            query: Case-insensitive search string.

        Returns:
            Matching entity state objects.
        """

        async with client:
            states: list[dict[str, Any]] = await client.get("/api/states")

        query_lower = query.lower()
        results = []
        for entity in states:
            entity_id: str = entity.get("entity_id", "")
            friendly_name: str = entity.get("attributes", {}).get("friendly_name", "")
            state: str = entity.get("state", "")

            if any(
                query_lower in field.lower()
                for field in [entity_id, friendly_name, state]
            ):
                results.append(entity)

        return results

    @mcp.tool()
    async def list_services() -> dict[str, Any]:
        """
        List all available Home Assistant services grouped by domain.

        Useful for discovering what ``domain`` and ``service`` values to pass to
        ``call_service``, and what parameters each service accepts.

        Returns:
            Dictionary mapping domain names to their available services and schemas.
        """

        async with client:
            return await client.get("/api/services")

    @mcp.tool()
    async def list_areas() -> list[dict[str, Any]]:
        """
        List all configured areas in Home Assistant.

        Areas are logical groupings of devices and entities (e.g. "Living Room",
        "Kitchen"). The returned ``area_id`` values can be used with
        ``list_entity_registry`` to filter entities by area.

        Returns:
            List of area objects with ``area_id`` and ``name``.
        """

        template = (
            "{%- set ns = namespace(areas=[]) -%}"
            "{%- for area_id in areas() -%}"
            "{%- set ns.areas = ns.areas"
            " + [{'area_id': area_id, 'name': area_name(area_id)}] -%}"
            "{%- endfor -%}"
            "{{ ns.areas | tojson }}"
        )

        async with client:
            result = await client.post("/api/template", {"template": template})

        if isinstance(result, list):
            return result

        return json.loads(result)

    @mcp.tool()
    async def list_devices() -> list[dict[str, Any]]:
        """
        List all entities with their friendly names and area assignments.

        Combines live state data (for friendly names and current state) with the
        HA template engine (for area assignments). Every entity in the state
        machine is returned regardless of whether it belongs to an area.
        Entities without a configured friendly name fall back to their
        ``entity_id``. Entities not assigned to any area will have ``area_id``
        and ``area_name`` set to ``null``.

        Returns:
            List of objects with ``entity_id``, ``friendly_name``, ``state``,
            ``area_id``, and ``area_name``.
        """

        async with client:
            area_result = await client.post(
                "/api/template", {"template": _AREA_ENTITIES_TEMPLATE}
            )

        async with client:
            states: list[dict[str, Any]] = await client.get("/api/states")

        area_entries: list[dict[str, Any]] = (
            area_result if isinstance(area_result, list) else json.loads(area_result)
        )

        area_map = {entry["entity_id"]: entry for entry in area_entries}

        return [
            {
                "entity_id": state["entity_id"],
                "friendly_name": state.get("attributes", {}).get(
                    "friendly_name", state["entity_id"]
                ),
                "state": state.get("state"),
                "area_id": area_map.get(state["entity_id"], {}).get("area_id"),
                "area_name": area_map.get(state["entity_id"], {}).get("area_name"),
            }
            for state in states
        ]

    @mcp.tool()
    async def list_entity_registry() -> list[dict[str, Any]]:
        """
        List entities that are assigned to an area, with friendly names
        and current state.

        Unlike ``list_devices``, this tool returns **only** entities that have an
        area assignment, which is useful for queries scoped to a room or zone. Friendly
        names are sourced from live state. Entities without a configured friendly
        name fall back to their ``entity_id``.

        Returns:
            List of objects with ``entity_id``, ``friendly_name``, ``state``,
            ``area_id``, and ``area_name``.
        """

        async with client:
            area_result = await client.post(
                "/api/template", {"template": _AREA_ENTITIES_TEMPLATE}
            )

        async with client:
            states: list[dict[str, Any]] = await client.get("/api/states")

        area_entries: list[dict[str, Any]] = (
            area_result if isinstance(area_result, list) else json.loads(area_result)
        )

        state_map = {s["entity_id"]: s for s in states}

        return [
            {
                "entity_id": entry["entity_id"],
                "friendly_name": state_map.get(entry["entity_id"], {})
                .get("attributes", {})
                .get("friendly_name", entry["entity_id"]),
                "state": state_map.get(entry["entity_id"], {}).get("state"),
                "area_id": entry["area_id"],
                "area_name": entry["area_name"],
            }
            for entry in area_entries
        ]

    @mcp.tool()
    async def get_entity_history(
        entity_id: str,
        start_time: str | None = None,
        end_time: str | None = None,
    ) -> list[list[dict[str, Any]]]:
        """
        Retrieve the historical state changes for an entity.

        Queries the HA history API. When ``start_time`` is omitted, HA defaults
        to the past 24 hours. Each inner list in the response corresponds to one
        entity (only one entity is requested here, so the outer list will
        normally contain a single element).

        Args:
            entity_id: Full entity ID, e.g. ``sensor.temperature``.
            start_time: ISO 8601 timestamp for the start of the range,
                e.g. ``2024-01-01T00:00:00``.
            end_time: ISO 8601 timestamp for the end of the range.

        Returns:
            List of lists of historical state objects, one inner list per entity.
        """

        path = "/api/history/period"
        if start_time:
            path = f"{path}/{start_time}"

        params: dict[str, str] = {"filter_entity_id": entity_id}
        if end_time:
            params["end_time"] = end_time

        async with client:
            return await client.get(path, params=params)

    @mcp.tool()
    async def get_logbook(
        entity_id: str | None = None,
        start_time: str | None = None,
        end_time: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Fetch logbook entries, optionally filtered by entity and time range.

        The logbook records human-readable events such as state changes,
        service calls, and automation triggers. When no filters are provided,
        HA returns entries for the past 24 hours across all entities. Filtering
        by ``entity_id`` narrows results to events involving that specific entity.

        Args:
            entity_id: Optional entity ID to filter entries.
            start_time: ISO 8601 start timestamp.
            end_time: ISO 8601 end timestamp.

        Returns:
            List of logbook entry objects.
        """

        path = "/api/logbook"
        if start_time:
            path = f"{path}/{start_time}"

        params: dict[str, str] = {}
        if entity_id:
            params["entity"] = entity_id
        if end_time:
            params["end_time"] = end_time

        async with client:
            return await client.get(path, params=params or None)

    @mcp.tool()
    async def render_template(template: str) -> str:
        """
        Render a Jinja2 template string using Home Assistant's template engine.

        Gives access to the full set of HA template functions and filters
        (``states()``, ``is_state()``, ``area_entities()``, ``now()``, etc.).
        Useful for building dynamic queries or aggregations that aren't directly
        exposed by other tools.

        Args:
            template: A Jinja2 template string,
                e.g. ``{{ states('sensor.temperature') }}``.

        Returns:
            The rendered string result.
        """

        async with client:
            return await client.post("/api/template", {"template": template})

    @mcp.tool()
    async def fire_event(
        event_type: str, event_data: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Fire a custom event on the Home Assistant event bus.

        Any automation or integration listening for ``event_type`` will be
        triggered. This is an advanced tool intended for custom integrations and
        automations that respond to named events. Most device control should go
        through ``call_service`` instead.

        Args:
            event_type: Name of the event to fire, e.g. ``my_custom_event``.
            event_data: Optional dictionary of data to include with the event.

        Returns:
            Confirmation message from HA.
        """

        async with client:
            return await client.post(f"/api/events/{event_type}", event_data or {})
