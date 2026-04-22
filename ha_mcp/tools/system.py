"""MCP tools for Home Assistant system information, configuration, and updates."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from mcp.server.fastmcp import Context
from mcp.types import ToolAnnotations

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

    from ha_mcp.client import HomeAssistantClient

_SUPERVISOR_PREFIX = "/api/hassio"


def register(mcp: FastMCP) -> None:
    """Register all system and configuration tools on the MCP server."""

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=True))
    async def get_ha_config(ctx: Context) -> dict[str, Any]:
        """
        Get the current Home Assistant core configuration.

        Args:
            ctx: MCP request context (injected by FastMCP).

        Returns:
            Config object including version, location_name, latitude,
            longitude, unit_system, time_zone, components, and more.
        """

        client: HomeAssistantClient = ctx.request_context.lifespan_context.client
        return await client.get("/api/config")

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=True))
    async def check_config(ctx: Context) -> dict[str, Any]:
        """
        Validate the Home Assistant YAML configuration files.

        Args:
            ctx: MCP request context (injected by FastMCP).

        Returns:
            Validation result with result ("valid" or "invalid") and an errors
            list of human-readable strings describing each problem, including
            YAML parse errors and unknown keys.
        """

        client: HomeAssistantClient = ctx.request_context.lifespan_context.client
        return await client.post("/api/config/core/check_config")

    @mcp.tool(annotations=ToolAnnotations(destructiveHint=True, openWorldHint=True))
    async def restart_ha(ctx: Context) -> str:
        """
        Restart the Home Assistant Core process.

        Args:
            ctx: MCP request context (injected by FastMCP).

        Returns:
            Confirmation message.
        """

        client: HomeAssistantClient = ctx.request_context.lifespan_context.client
        result = await client.post("/api/config/core/restart")
        return str(result)

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=True))
    async def get_supervisor_info(ctx: Context) -> dict[str, Any]:
        """
        Get Supervisor system information including version and update status.

        Requires a Supervisor-enabled installation (HA OS or Supervised). Use
        the returned version_latest field to decide whether to call
        update_supervisor.

        Args:
            ctx: MCP request context (injected by FastMCP).

        Returns:
            Supervisor info dict with versions, channel, and update availability.
        """

        client: HomeAssistantClient = ctx.request_context.lifespan_context.client
        response: dict[str, Any] = await client.get(
            f"{_SUPERVISOR_PREFIX}/supervisor/info"
        )
        return response.get("data", response)

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=True))
    async def get_core_info(ctx: Context) -> dict[str, Any]:
        """
        Get Home Assistant Core process information via the Supervisor.

        Requires a Supervisor-enabled installation (HA OS or Supervised). Use
        the returned version_latest field to decide whether to call update_core.

        Args:
            ctx: MCP request context (injected by FastMCP).

        Returns:
            Core info including version, update availability, and boot state.
        """

        client: HomeAssistantClient = ctx.request_context.lifespan_context.client
        response: dict[str, Any] = await client.get(
            f"{_SUPERVISOR_PREFIX}/core/info"
        )
        return response.get("data", response)

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=True))
    async def get_host_info(ctx: Context) -> dict[str, Any]:
        """
        Get information about the underlying host OS.

        Requires a Supervisor-enabled installation (HA OS or Supervised).

        Args:
            ctx: MCP request context (injected by FastMCP).

        Returns:
            Host info including hostname, OS version, CPU usage, and memory.
        """

        client: HomeAssistantClient = ctx.request_context.lifespan_context.client
        response: dict[str, Any] = await client.get(
            f"{_SUPERVISOR_PREFIX}/host/info"
        )
        return response.get("data", response)

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=True))
    async def get_os_info(ctx: Context) -> dict[str, Any]:
        """
        Get Home Assistant OS information and update status.

        Requires a Supervisor-enabled installation (HA OS or Supervised). Use
        the returned version_latest field to decide whether to call update_os.

        Args:
            ctx: MCP request context (injected by FastMCP).

        Returns:
            OS info with version and update availability.
        """

        client: HomeAssistantClient = ctx.request_context.lifespan_context.client
        response: dict[str, Any] = await client.get(f"{_SUPERVISOR_PREFIX}/os/info")
        return response.get("data", response)

    @mcp.tool(annotations=ToolAnnotations(openWorldHint=True))
    async def update_core(ctx: Context) -> str:
        """
        Update the Home Assistant Core to the latest available version.

        Requires a Supervisor-enabled installation (HA OS or Supervised). Call
        get_core_info first to confirm an update is available.

        Args:
            ctx: MCP request context (injected by FastMCP).

        Returns:
            Confirmation message.
        """

        client: HomeAssistantClient = ctx.request_context.lifespan_context.client
        response: dict[str, Any] = await client.post(
            f"{_SUPERVISOR_PREFIX}/core/update"
        )
        return response.get("result", str(response))

    @mcp.tool(annotations=ToolAnnotations(openWorldHint=True))
    async def update_supervisor(ctx: Context) -> str:
        """
        Update the Home Assistant Supervisor to the latest version.

        Requires a Supervisor-enabled installation (HA OS or Supervised). Call
        get_supervisor_info first to confirm an update is available.

        Args:
            ctx: MCP request context (injected by FastMCP).

        Returns:
            Confirmation message.
        """

        client: HomeAssistantClient = ctx.request_context.lifespan_context.client
        response: dict[str, Any] = await client.post(
            f"{_SUPERVISOR_PREFIX}/supervisor/update"
        )
        return response.get("result", str(response))

    @mcp.tool(annotations=ToolAnnotations(openWorldHint=True))
    async def update_os(ctx: Context) -> str:
        """
        Update the Home Assistant OS to the latest version.

        Requires a Supervisor-enabled installation (HA OS or Supervised). Call
        get_os_info first to confirm an update is available.

        Args:
            ctx: MCP request context (injected by FastMCP).

        Returns:
            Confirmation message.
        """

        client: HomeAssistantClient = ctx.request_context.lifespan_context.client
        response: dict[str, Any] = await client.post(
            f"{_SUPERVISOR_PREFIX}/os/update"
        )
        return response.get("result", str(response))

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=True))
    async def list_integrations(ctx: Context) -> list[dict[str, Any]]:
        """
        List all installed Home Assistant integrations.

        Args:
            ctx: MCP request context (injected by FastMCP).

        Returns:
            List of integration config entries with domain,
            title, and state.
        """

        client: HomeAssistantClient = ctx.request_context.lifespan_context.client
        return await client.get("/api/config/config_entries/entry")

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=True))
    async def get_system_health(ctx: Context) -> dict[str, Any]:
        """
        Get system health information for all components.

        Args:
            ctx: MCP request context (injected by FastMCP).

        Returns:
            Health data keyed by component domain with status and metadata.
        """

        client: HomeAssistantClient = ctx.request_context.lifespan_context.client
        return await client.get("/api/system_health")

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=True))
    async def list_users(ctx: Context) -> list[dict[str, Any]]:
        """
        List all user accounts in Home Assistant.

        Args:
            ctx: MCP request context (injected by FastMCP).

        Returns:
            List of user objects with id, name, is_active, and is_admin.
        """

        client: HomeAssistantClient = ctx.request_context.lifespan_context.client
        return await client.get("/api/config/auth/users")

    @mcp.tool(annotations=ToolAnnotations(openWorldHint=True))
    async def create_backup(ctx: Context) -> dict[str, Any]:
        """
        Trigger the creation of a full Home Assistant backup.

        Requires a Supervisor-enabled installation (HA OS or Supervised).

        Args:
            ctx: MCP request context (injected by FastMCP).

        Returns:
            Backup job info including the backup slug.
        """

        client: HomeAssistantClient = ctx.request_context.lifespan_context.client
        response: dict[str, Any] = await client.post(
            f"{_SUPERVISOR_PREFIX}/backups/new/full"
        )
        return response.get("data", response)

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=True))
    async def list_backups(ctx: Context) -> list[dict[str, Any]]:
        """
        List all available Home Assistant backups.

        Requires a Supervisor-enabled installation (HA OS or Supervised).

        Args:
            ctx: MCP request context (injected by FastMCP).

        Returns:
            List of backup objects with slug, name, date, size, and type.
        """

        client: HomeAssistantClient = ctx.request_context.lifespan_context.client
        response: dict[str, Any] = await client.get(f"{_SUPERVISOR_PREFIX}/backups")
        return response.get("data", {}).get("backups", [])
