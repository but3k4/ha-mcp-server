"""MCP tools for Home Assistant automation and script management."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from mcp.server.fastmcp import Context
from mcp.types import ToolAnnotations

from ha_mcp.client import HomeAssistantError

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

    from ha_mcp.client import HomeAssistantClient


def register(mcp: FastMCP) -> None:
    """Register all automation and script tools on the MCP server."""

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=True))
    async def list_automations(ctx: Context) -> list[dict[str, Any]] | str:
        """
        List all automations defined in Home Assistant.

        Args:
            ctx: MCP request context (injected by FastMCP).

        Returns:
            List of automation state objects. Each has ``entity_id``,
            ``state`` (``on``/``off``), and ``attributes`` with
            ``friendly_name`` and ``last_triggered``.
        """

        client: HomeAssistantClient = ctx.request_context.lifespan_context.client
        try:
            states: list[dict[str, Any]] = await client.get("/api/states")
        except HomeAssistantError as exc:
            return f"Error: {exc}"
        return [s for s in states if s["entity_id"].startswith("automation.")]

    @mcp.tool(annotations=ToolAnnotations(openWorldHint=True))
    async def trigger_automation(
        ctx: Context, entity_id: str
    ) -> list[dict[str, Any]] | str:
        """
        Manually trigger an automation regardless of its conditions.

        Args:
            ctx: MCP request context (injected by FastMCP).
            entity_id: Automation entity ID, e.g. ``automation.morning_lights``.

        Returns:
            List of affected entity states.
        """

        client: HomeAssistantClient = ctx.request_context.lifespan_context.client
        try:
            return await client.post(
                "/api/services/automation/trigger",
                {"entity_id": entity_id},
            )
        except HomeAssistantError as exc:
            return f"Error: {exc}"

    @mcp.tool(annotations=ToolAnnotations(openWorldHint=True))
    async def enable_automation(
        ctx: Context, entity_id: str
    ) -> list[dict[str, Any]] | str:
        """
        Enable a previously disabled automation.

        Args:
            ctx: MCP request context (injected by FastMCP).
            entity_id: Automation entity ID, e.g. ``automation.morning_lights``.

        Returns:
            List of affected entity states.
        """

        client: HomeAssistantClient = ctx.request_context.lifespan_context.client
        try:
            return await client.post(
                "/api/services/automation/turn_on",
                {"entity_id": entity_id},
            )
        except HomeAssistantError as exc:
            return f"Error: {exc}"

    @mcp.tool(annotations=ToolAnnotations(openWorldHint=True))
    async def disable_automation(
        ctx: Context, entity_id: str
    ) -> list[dict[str, Any]] | str:
        """
        Disable an automation so it will not fire automatically.

        Args:
            ctx: MCP request context (injected by FastMCP).
            entity_id: Automation entity ID.

        Returns:
            List of affected entity states.
        """

        client: HomeAssistantClient = ctx.request_context.lifespan_context.client
        try:
            return await client.post(
                "/api/services/automation/turn_off",
                {"entity_id": entity_id},
            )
        except HomeAssistantError as exc:
            return f"Error: {exc}"

    @mcp.tool(annotations=ToolAnnotations(openWorldHint=True))
    async def reload_automations(ctx: Context) -> str:
        """
        Reload all automations from the YAML configuration without restarting HA.

        Args:
            ctx: MCP request context (injected by FastMCP).

        Returns:
            Confirmation message.
        """

        client: HomeAssistantClient = ctx.request_context.lifespan_context.client
        try:
            result = await client.post("/api/services/automation/reload")
        except HomeAssistantError as exc:
            return f"Error: {exc}"
        return f"Automations reloaded. Affected states: {len(result)}"

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=True))
    async def list_scripts(ctx: Context) -> list[dict[str, Any]] | str:
        """
        List all scripts defined in Home Assistant.

        Args:
            ctx: MCP request context (injected by FastMCP).

        Returns:
            List of script state objects with ``entity_id``, ``state``,
            and ``attributes``.
        """

        client: HomeAssistantClient = ctx.request_context.lifespan_context.client
        try:
            states: list[dict[str, Any]] = await client.get("/api/states")
        except HomeAssistantError as exc:
            return f"Error: {exc}"
        return [s for s in states if s["entity_id"].startswith("script.")]

    @mcp.tool(annotations=ToolAnnotations(openWorldHint=True))
    async def run_script(
        ctx: Context,
        entity_id: str,
        variables: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]] | str:
        """
        Execute a HA script entity.

        Args:
            ctx: MCP request context (injected by FastMCP).
            entity_id: Script entity ID, e.g. ``script.goodnight``.
            variables: Optional variables to pass into the script.

        Returns:
            List of affected entity states.
        """

        client: HomeAssistantClient = ctx.request_context.lifespan_context.client
        payload: dict[str, Any] = {"entity_id": entity_id}
        if variables:
            payload["variables"] = variables

        try:
            return await client.post("/api/services/script/turn_on", payload)
        except HomeAssistantError as exc:
            return f"Error: {exc}"

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=True))
    async def list_scenes(ctx: Context) -> list[dict[str, Any]] | str:
        """
        List all scenes defined in Home Assistant.

        Args:
            ctx: MCP request context (injected by FastMCP).

        Returns:
            List of scene state objects.
        """

        client: HomeAssistantClient = ctx.request_context.lifespan_context.client
        try:
            states: list[dict[str, Any]] = await client.get("/api/states")
        except HomeAssistantError as exc:
            return f"Error: {exc}"
        return [s for s in states if s["entity_id"].startswith("scene.")]

    @mcp.tool(annotations=ToolAnnotations(openWorldHint=True))
    async def activate_scene(
        ctx: Context, entity_id: str
    ) -> list[dict[str, Any]] | str:
        """
        Activate a Home Assistant scene.

        Args:
            ctx: MCP request context (injected by FastMCP).
            entity_id: Scene entity ID, e.g. ``scene.movie_time``.

        Returns:
            List of affected entity states.
        """

        client: HomeAssistantClient = ctx.request_context.lifespan_context.client
        try:
            return await client.post(
                "/api/services/scene/turn_on",
                {"entity_id": entity_id},
            )
        except HomeAssistantError as exc:
            return f"Error: {exc}"
