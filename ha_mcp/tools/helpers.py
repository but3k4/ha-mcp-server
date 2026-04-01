"""
MCP tools for Home Assistant input helpers and timers.

Covers the ``input_boolean``, ``input_number``, ``input_select``,
``input_text``, ``input_datetime``, ``input_button``, and ``timer`` domains.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

    from ha_mcp.client import HomeAssistantClient

_HELPER_DOMAINS = frozenset(
    {
        "input_boolean",
        "input_button",
        "input_datetime",
        "input_number",
        "input_select",
        "input_text",
        "timer",
    }
)


def register(mcp: FastMCP, client: HomeAssistantClient) -> None:
    """
    Register all input helper and timer tools on the MCP server.

    Args:
        mcp: The FastMCP server instance to register tools on.
        client: The authenticated Home Assistant client.
    """

    @mcp.tool()
    async def list_input_helpers(domain: str | None = None) -> list[dict[str, Any]]:
        """
        List Home Assistant input helper and timer entities.

        Returns entities from the virtual-device domains: ``input_boolean``,
        ``input_button``, ``input_datetime``, ``input_number``,
        ``input_select``, ``input_text``, and ``timer``. When ``domain`` is
        provided only entities of that specific type are returned.

        Args:
            domain: Optional domain filter, e.g. ``input_boolean`` or ``timer``.

        Returns:
            List of entity state objects for the matching helper domains.
        """

        async with client:
            states: list[dict[str, Any]] = await client.get("/api/states")

        if domain is not None:
            return [s for s in states if s["entity_id"].startswith(f"{domain}.")]

        return [s for s in states if s["entity_id"].split(".")[0] in _HELPER_DOMAINS]

    @mcp.tool()
    async def set_input_boolean(entity_id: str, state: str) -> list[dict[str, Any]]:
        """
        Turn an ``input_boolean`` helper on or off.

        Args:
            entity_id: Input boolean entity ID, e.g. ``input_boolean.vacation_mode``.
            state: Target state — must be ``"on"`` or ``"off"``.

        Returns:
            List of affected entity states.

        Raises:
            ValueError: If ``state`` is not ``"on"`` or ``"off"``.
        """

        if state not in ("on", "off"):
            raise ValueError(f"state must be 'on' or 'off', got {state!r}")

        service = "turn_on" if state == "on" else "turn_off"

        async with client:
            return await client.post(
                f"/api/services/input_boolean/{service}",
                {"entity_id": entity_id},
            )

    @mcp.tool()
    async def set_input_number(entity_id: str, value: float) -> list[dict[str, Any]]:
        """
        Set the numeric value of an ``input_number`` helper.

        The value must be within the min/max range configured for the entity.
        Use ``get_entity`` to inspect the ``min``, ``max``, and ``step``
        attributes before calling this. HA enforces the range server-side and
        will raise ``HomeAssistantError`` if the value is out of bounds.

        Args:
            entity_id: Input number entity ID, e.g. ``input_number.target_temp``.
            value: New numeric value.

        Returns:
            List of affected entity states.
        """

        async with client:
            return await client.post(
                "/api/services/input_number/set_value",
                {"entity_id": entity_id, "value": value},
            )

    @mcp.tool()
    async def set_input_select(entity_id: str, option: str) -> list[dict[str, Any]]:
        """
        Select an option on an ``input_select`` helper.

        The option must exactly match one of the values listed in the entity's
        ``options`` attribute (case-sensitive). Use ``get_entity`` to retrieve
        the available options first. HA will raise ``HomeAssistantError`` if
        the option does not exist in the configured list.

        Args:
            entity_id: Input select entity ID, e.g. ``input_select.preset_mode``.
            option: Option string to select, e.g. ``"Away"``.

        Returns:
            List of affected entity states.
        """

        async with client:
            return await client.post(
                "/api/services/input_select/select_option",
                {"entity_id": entity_id, "option": option},
            )

    @mcp.tool()
    async def set_input_text(entity_id: str, value: str) -> list[dict[str, Any]]:
        """
        Set the text value of an ``input_text`` helper.

        The value must satisfy the min/max length and optional pattern
        constraints configured for the entity.

        Args:
            entity_id: Input text entity ID, e.g. ``input_text.welcome_message``.
            value: New text value.

        Returns:
            List of affected entity states.
        """

        async with client:
            return await client.post(
                "/api/services/input_text/set_value",
                {"entity_id": entity_id, "value": value},
            )

    @mcp.tool()
    async def set_input_datetime(
        entity_id: str,
        date: str | None = None,
        time: str | None = None,
        datetime_str: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Set the value of an ``input_datetime`` helper.

        Supply whichever of ``date``, ``time``, or ``datetime_str`` matches
        the entity's configured mode: ``date`` for date-only, ``time`` for
        time-only, ``datetime_str`` for combined date+time. Check the
        entity's ``has_date`` and ``has_time`` attributes via ``get_entity``
        to determine the mode. Passing a field the entity does not support
        will be silently ignored by Home Assistant.

        Args:
            entity_id: Input datetime entity ID, e.g. ``input_datetime.alarm_time``.
            date: Date string in ``YYYY-MM-DD`` format.
            time: Time string in ``HH:MM:SS`` format.
            datetime_str: Combined datetime in ``YYYY-MM-DD HH:MM:SS`` format.

        Returns:
            List of affected entity states.
        """

        payload: dict[str, Any] = {"entity_id": entity_id}
        if date is not None:
            payload["date"] = date
        if time is not None:
            payload["time"] = time
        if datetime_str is not None:
            payload["datetime"] = datetime_str

        async with client:
            return await client.post("/api/services/input_datetime/set_datetime", payload)

    @mcp.tool()
    async def start_timer(entity_id: str, duration: str | None = None) -> list[dict[str, Any]]:
        """
        Start or restart a ``timer`` entity.

        If ``duration`` is omitted the timer uses its configured default
        duration. Calling start on an already-running timer restarts it.

        Args:
            entity_id: Timer entity ID, e.g. ``timer.cooking``.
            duration: Optional override duration in ``HH:MM:SS`` or ``SS`` format,
                e.g. ``"00:05:00"`` for five minutes.

        Returns:
            List of affected entity states.
        """

        payload: dict[str, Any] = {"entity_id": entity_id}
        if duration is not None:
            payload["duration"] = duration

        async with client:
            return await client.post("/api/services/timer/start", payload)

    @mcp.tool()
    async def pause_timer(entity_id: str) -> list[dict[str, Any]]:
        """
        Pause a running ``timer`` entity.

        The remaining time is preserved. Use ``start_timer`` to resume.

        Args:
            entity_id: Timer entity ID, e.g. ``timer.cooking``.

        Returns:
            List of affected entity states.
        """

        async with client:
            return await client.post("/api/services/timer/pause", {"entity_id": entity_id})

    @mcp.tool()
    async def cancel_timer(entity_id: str) -> list[dict[str, Any]]:
        """
        Cancel a running or paused ``timer`` entity.

        The timer is reset to its configured duration. No ``timer.finished``
        event is fired.

        Args:
            entity_id: Timer entity ID, e.g. ``timer.cooking``.

        Returns:
            List of affected entity states.
        """

        async with client:
            return await client.post("/api/services/timer/cancel", {"entity_id": entity_id})
