"""MCP tools for accessing Home Assistant system and component logs."""

from __future__ import annotations

from typing import TYPE_CHECKING

from mcp.server.fastmcp import Context
from mcp.types import ToolAnnotations

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

    from ha_mcp.client import HomeAssistantClient

_SUPERVISOR_PREFIX = "/api/hassio"


def register(mcp: FastMCP) -> None:
    """Register all log-access tools on the MCP server."""

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=True))
    async def get_error_log(ctx: Context) -> str:
        """
        Get the Home Assistant core error log.

        Args:
            ctx: MCP request context (injected by FastMCP).

        Returns:
            Raw error log text from the HA logger.
        """

        client: HomeAssistantClient = ctx.request_context.lifespan_context.client
        return await client.get("/api/error_log")

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=True))
    async def get_supervisor_logs(ctx: Context) -> str:
        """
        Get logs from the Home Assistant Supervisor process.

        Requires a Supervisor-enabled installation (HA OS or Supervised).

        Args:
            ctx: MCP request context (injected by FastMCP).

        Returns:
            Raw Supervisor log output.
        """

        client: HomeAssistantClient = ctx.request_context.lifespan_context.client
        return await client.get(f"{_SUPERVISOR_PREFIX}/supervisor/logs")

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=True))
    async def get_core_logs(ctx: Context) -> str:
        """
        Get logs from the Home Assistant Core process via Supervisor.

        Requires a Supervisor-enabled installation (HA OS or Supervised).

        Args:
            ctx: MCP request context (injected by FastMCP).

        Returns:
            Raw Core process log output.
        """

        client: HomeAssistantClient = ctx.request_context.lifespan_context.client
        return await client.get(f"{_SUPERVISOR_PREFIX}/core/logs")

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=True))
    async def get_host_logs(ctx: Context) -> str:
        """
        Get system-level host logs from the underlying OS.

        Requires a Supervisor-enabled installation (HA OS or Supervised).

        Args:
            ctx: MCP request context (injected by FastMCP).

        Returns:
            Raw host/journald log output.
        """

        client: HomeAssistantClient = ctx.request_context.lifespan_context.client
        return await client.get(f"{_SUPERVISOR_PREFIX}/host/logs")

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=True))
    async def get_multicast_logs(ctx: Context) -> str:
        """
        Get logs from the Home Assistant Multicast service.

        Requires a Supervisor-enabled installation (HA OS or Supervised).

        Args:
            ctx: MCP request context (injected by FastMCP).

        Returns:
            Raw Multicast service log output.
        """

        client: HomeAssistantClient = ctx.request_context.lifespan_context.client
        return await client.get(f"{_SUPERVISOR_PREFIX}/multicast/logs")
