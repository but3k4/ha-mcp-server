"""
MCP tools for accessing Home Assistant system and component logs.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

    from ha_mcp.client import HomeAssistantClient

_SUPERVISOR_PREFIX = "/api/hassio"


def register(mcp: FastMCP, client: HomeAssistantClient) -> None:
    """
    Register all log-access tools on the MCP server.

    Args:
        mcp: The FastMCP server instance to register tools on.
        client: The authenticated Home Assistant client.
    """

    @mcp.tool()
    async def get_error_log() -> str:
        """
        Get the Home Assistant core error log.

        Returns:
            Raw error log text from the HA logger.
        """

        async with client:
            return await client.get("/api/error_log")

    @mcp.tool()
    async def get_supervisor_logs() -> str:
        """
        Get logs from the Home Assistant Supervisor process.

        Requires a Supervisor-enabled installation (HA OS or Supervised).
        Raises ``HomeAssistantError`` on HA Container or Core.

        Returns:
            Raw Supervisor log output.
        """

        async with client:
            return await client.get(f"{_SUPERVISOR_PREFIX}/supervisor/logs")

    @mcp.tool()
    async def get_core_logs() -> str:
        """
        Get logs from the Home Assistant Core process via Supervisor.

        Requires a Supervisor-enabled installation (HA OS or Supervised).
        Raises ``HomeAssistantError`` on HA Container or Core.

        Returns:
            Raw Core process log output.
        """

        async with client:
            return await client.get(f"{_SUPERVISOR_PREFIX}/core/logs")

    @mcp.tool()
    async def get_host_logs() -> str:
        """
        Get system-level host logs from the underlying OS.

        Requires a Supervisor-enabled installation (HA OS or Supervised).
        Raises ``HomeAssistantError`` on HA Container or Core.

        Returns:
            Raw host/journald log output.
        """

        async with client:
            return await client.get(f"{_SUPERVISOR_PREFIX}/host/logs")

    @mcp.tool()
    async def get_multicast_logs() -> str:
        """
        Get logs from the Home Assistant Multicast service.

        Requires a Supervisor-enabled installation (HA OS or Supervised).
        Raises ``HomeAssistantError`` on HA Container or Core.

        Returns:
            Raw Multicast service log output.
        """

        async with client:
            return await client.get(f"{_SUPERVISOR_PREFIX}/multicast/logs")
