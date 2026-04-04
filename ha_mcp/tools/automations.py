"""
MCP tools for Home Assistant automation and script management.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

    from ha_mcp.client import HomeAssistantClient


def register(mcp: FastMCP, client: HomeAssistantClient) -> None:
    """
    Register all automation and script tools on the MCP server.

    Args:
        mcp: The FastMCP server instance to register tools on.
        client: The authenticated Home Assistant client.
    """

    @mcp.tool()
    async def list_automations() -> list[dict[str, Any]]:
        """
        List all automations defined in Home Assistant.

        Returns:
            List of automation state objects. Each has ``entity_id``,
            ``state`` (``on``/``off``), and ``attributes`` with
            ``friendly_name`` and ``last_triggered``.
        """

        async with client:
            states: list[dict[str, Any]] = await client.get("/api/states")

        return [s for s in states if s["entity_id"].startswith("automation.")]

    @mcp.tool()
    async def trigger_automation(entity_id: str) -> list[dict[str, Any]]:
        """
        Manually trigger an automation regardless of its conditions.

        Args:
            entity_id: Automation entity ID, e.g. ``automation.morning_lights``.

        Returns:
            List of affected entity states.
        """

        async with client:
            return await client.post(
                "/api/services/automation/trigger",
                {"entity_id": entity_id},
            )

    @mcp.tool()
    async def enable_automation(entity_id: str) -> list[dict[str, Any]]:
        """
        Enable a previously disabled automation.

        Args:
            entity_id: Automation entity ID, e.g. ``automation.morning_lights``.

        Returns:
            List of affected entity states.
        """

        async with client:
            return await client.post(
                "/api/services/automation/turn_on",
                {"entity_id": entity_id},
            )

    @mcp.tool()
    async def disable_automation(entity_id: str) -> list[dict[str, Any]]:
        """
        Disable an automation so it will not fire automatically.

        Args:
            entity_id: Automation entity ID.

        Returns:
            List of affected entity states.
        """

        async with client:
            return await client.post(
                "/api/services/automation/turn_off",
                {"entity_id": entity_id},
            )

    @mcp.tool()
    async def reload_automations() -> str:
        """
        Reload all automations from the YAML configuration without restarting HA.

        Returns:
            Confirmation message.
        """

        async with client:
            result = await client.post("/api/services/automation/reload")

        return f"Automations reloaded. Affected states: {len(result)}"

    @mcp.tool()
    async def list_scripts() -> list[dict[str, Any]]:
        """
        List all scripts defined in Home Assistant.

        Returns:
            List of script state objects with ``entity_id``, ``state``,
            and ``attributes``.
        """

        async with client:
            states: list[dict[str, Any]] = await client.get("/api/states")

        return [s for s in states if s["entity_id"].startswith("script.")]

    @mcp.tool()
    async def run_script(
        entity_id: str, variables: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """
        Execute a HA script entity.

        Args:
            entity_id: Script entity ID, e.g. ``script.goodnight``.
            variables: Optional variables to pass into the script.

        Returns:
            List of affected entity states.
        """

        payload: dict[str, Any] = {"entity_id": entity_id}
        if variables:
            payload["variables"] = variables

        async with client:
            return await client.post("/api/services/script/turn_on", payload)

    @mcp.tool()
    async def list_scenes() -> list[dict[str, Any]]:
        """
        List all scenes defined in Home Assistant.

        Returns:
            List of scene state objects.
        """

        async with client:
            states: list[dict[str, Any]] = await client.get("/api/states")

        return [s for s in states if s["entity_id"].startswith("scene.")]

    @mcp.tool()
    async def activate_scene(entity_id: str) -> list[dict[str, Any]]:
        """
        Activate a Home Assistant scene.

        Args:
            entity_id: Scene entity ID, e.g. ``scene.movie_time``.

        Returns:
            List of affected entity states.
        """

        async with client:
            return await client.post(
                "/api/services/scene/turn_on",
                {"entity_id": entity_id},
            )
