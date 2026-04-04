"""
MCP tools for Home Assistant system information, configuration, and updates.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

    from ha_mcp.client import HomeAssistantClient

_SUPERVISOR_PREFIX = "/api/hassio"


def register(mcp: FastMCP, client: HomeAssistantClient) -> None:
    """
    Register all system and configuration tools on the MCP server.

    Args:
        mcp: The FastMCP server instance to register tools on.
        client: The authenticated Home Assistant client.
    """

    @mcp.tool()
    async def get_ha_config() -> dict[str, Any]:
        """
        Get the current Home Assistant core configuration.

        Returns:
            Config object including ``version``, ``location_name``, ``latitude``,
            ``longitude``, ``unit_system``, ``time_zone``, ``components``, and more.
        """

        async with client:
            return await client.get("/api/config")

    @mcp.tool()
    async def check_config() -> dict[str, Any]:
        """
        Validate the Home Assistant YAML configuration files.

        Returns:
            Validation result with ``result`` (``"valid"`` or ``"invalid"``) and
            an ``errors`` list of human-readable strings describing each problem,
            including YAML parse errors and unknown keys.
        """

        async with client:
            return await client.post("/api/config/core/check_config")

    @mcp.tool()
    async def restart_ha() -> str:
        """
        Restart the Home Assistant Core process.

        Returns:
            Confirmation message.
        """

        async with client:
            result = await client.post("/api/config/core/restart")

        return str(result)

    @mcp.tool()
    async def get_supervisor_info() -> dict[str, Any]:
        """
        Get Supervisor system information including version and update status.

        Requires a Supervisor-enabled installation (HA OS or Supervised).
        Raises ``HomeAssistantError`` on HA Container or Core. Use the
        returned ``version_latest`` field to decide whether to call
        ``update_supervisor``.

        Returns:
            Supervisor info dict with versions, channel, and update availability.
        """

        async with client:
            response: dict[str, Any] = await client.get(
                f"{_SUPERVISOR_PREFIX}/supervisor/info"
            )

        return response.get("data", response)

    @mcp.tool()
    async def get_core_info() -> dict[str, Any]:
        """
        Get Home Assistant Core process information via the Supervisor.

        Requires a Supervisor-enabled installation (HA OS or Supervised).
        Raises ``HomeAssistantError`` on HA Container or Core. Use the
        returned ``version_latest`` field to decide whether to call
        ``update_core``.

        Returns:
            Core info including version, update availability, and boot state.
        """

        async with client:
            response: dict[str, Any] = await client.get(
                f"{_SUPERVISOR_PREFIX}/core/info"
            )

        return response.get("data", response)

    @mcp.tool()
    async def get_host_info() -> dict[str, Any]:
        """
        Get information about the underlying host OS.

        Requires a Supervisor-enabled installation (HA OS or Supervised).
        Raises ``HomeAssistantError`` on HA Container or Core.

        Returns:
            Host info including hostname, OS version, CPU usage, and memory.
        """

        async with client:
            response: dict[str, Any] = await client.get(
                f"{_SUPERVISOR_PREFIX}/host/info"
            )

        return response.get("data", response)

    @mcp.tool()
    async def get_os_info() -> dict[str, Any]:
        """
        Get Home Assistant OS information and update status.

        Requires a Supervisor-enabled installation (HA OS or Supervised).
        Raises ``HomeAssistantError`` on HA Container or Core. Use the
        returned ``version_latest`` field to decide whether to call
        ``update_os``.

        Returns:
            OS info with version and update availability.
        """

        async with client:
            response: dict[str, Any] = await client.get(f"{_SUPERVISOR_PREFIX}/os/info")

        return response.get("data", response)

    @mcp.tool()
    async def update_core() -> str:
        """
        Update the Home Assistant Core to the latest available version.

        Requires a Supervisor-enabled installation (HA OS or Supervised).
        Raises ``HomeAssistantError`` on HA Container or Core. Call
        ``get_core_info`` first to confirm an update is available.

        Returns:
            Confirmation message.
        """

        async with client:
            response: dict[str, Any] = await client.post(
                f"{_SUPERVISOR_PREFIX}/core/update"
            )

        return response.get("result", str(response))

    @mcp.tool()
    async def update_supervisor() -> str:
        """
        Update the Home Assistant Supervisor to the latest version.

        Requires a Supervisor-enabled installation (HA OS or Supervised).
        Raises ``HomeAssistantError`` on HA Container or Core. Call
        ``get_supervisor_info`` first to confirm an update is available.

        Returns:
            Confirmation message.
        """

        async with client:
            response: dict[str, Any] = await client.post(
                f"{_SUPERVISOR_PREFIX}/supervisor/update"
            )

        return response.get("result", str(response))

    @mcp.tool()
    async def update_os() -> str:
        """
        Update the Home Assistant OS to the latest version.

        Requires a Supervisor-enabled installation (HA OS or Supervised).
        Raises ``HomeAssistantError`` on HA Container or Core. Call
        ``get_os_info`` first to confirm an update is available.

        Returns:
            Confirmation message.
        """

        async with client:
            response: dict[str, Any] = await client.post(
                f"{_SUPERVISOR_PREFIX}/os/update"
            )

        return response.get("result", str(response))

    @mcp.tool()
    async def list_integrations() -> list[dict[str, Any]]:
        """
        List all installed Home Assistant integrations.

        Returns:
            List of integration config entries with ``domain``,
            ``title``, and ``state``.
        """

        async with client:
            return await client.get("/api/config/config_entries/entry")

    @mcp.tool()
    async def reload_integration(entry_id: str) -> str:
        """
        Reload a specific integration config entry without restarting HA.

        Raises ``HomeAssistantError`` if the integration does not support
        reloading (not all integrations are reloadable). Use
        ``list_integrations`` to obtain the ``entry_id``.

        Args:
            entry_id: The config entry ID to reload (from ``list_integrations``).

        Returns:
            Confirmation message.
        """

        async with client:
            result = await client.post(
                f"/api/config/config_entries/entry/{entry_id}/reload"
            )

        return str(result)

    @mcp.tool()
    async def get_system_health() -> dict[str, Any]:
        """
        Get system health information for all components.

        Returns:
            Health data keyed by component domain with status and metadata.
        """

        async with client:
            return await client.get("/api/system_health")

    @mcp.tool()
    async def list_users() -> list[dict[str, Any]]:
        """
        List all user accounts in Home Assistant.

        Returns:
            List of user objects with ``id``, ``name``, ``is_active``, and ``is_admin``.
        """

        async with client:
            return await client.get("/api/config/auth/users")

    @mcp.tool()
    async def create_backup() -> dict[str, Any]:
        """
        Trigger the creation of a full Home Assistant backup.

        Returns:
            Backup job info including the backup slug.
        """

        async with client:
            response: dict[str, Any] = await client.post(
                f"{_SUPERVISOR_PREFIX}/backups/new/full"
            )

        return response.get("data", response)

    @mcp.tool()
    async def list_backups() -> list[dict[str, Any]]:
        """
        List all available Home Assistant backups.

        Returns:
            List of backup objects with ``slug``, ``name``, ``date``,
            ``size``, and ``type``.
        """

        async with client:
            response: dict[str, Any] = await client.get(f"{_SUPERVISOR_PREFIX}/backups")

        return response.get("data", {}).get("backups", [])
