"""
MCP tools for the Home Assistant device and config-entry registries.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

    from ha_mcp.client import HomeAssistantClient


def register(mcp: FastMCP, client: HomeAssistantClient) -> None:
    """
    Register all registry tools on the MCP server.

    Args:
        mcp: The FastMCP server instance to register tools on.
        client: The authenticated Home Assistant client.
    """

    @mcp.tool()
    async def get_device_registry() -> list[dict[str, Any]]:
        """
        List all devices in the Home Assistant device registry.

        Returns hardware-level device information sourced from the device
        registry, not the state machine. Each entry includes ``id``,
        ``name``, ``manufacturer``, ``model``, ``sw_version``,
        ``hw_version``, ``area_id``, and the list of ``config_entries``
        the device belongs to. Use this to identify physical devices by
        manufacturer and model rather than by entity ID.

        The HA REST API may return either a bare list or a dict with a
        ``devices`` key depending on the HA version; this tool normalises
        both forms to a plain list.

        Returns:
            List of device registry entries.
        """

        async with client:
            response: dict[str, Any] = await client.get("/api/config/device_registry/list")

        return response.get("devices", response) if isinstance(response, dict) else response

    @mcp.tool()
    async def list_config_entries() -> list[dict[str, Any]]:
        """
        List all integration config entries loaded in Home Assistant.

        Config entries represent installed integrations (e.g. Philips Hue,
        Google Cast, MQTT). Each entry includes ``entry_id``, ``domain``,
        ``title``, ``disabled_by``, and ``state``. Possible ``state`` values:
        ``loaded``, ``setup_error``, ``migration_error``, ``setup_retry``,
        ``failed_unload``, ``not_loaded``, ``disabled``. Use ``entry_id``
        with ``reload_config_entry`` to reload a specific integration without
        restarting HA.

        Returns:
            List of config entry objects.
        """

        async with client:
            return await client.get("/api/config/config_entries/entry")

    @mcp.tool()
    async def reload_config_entry(entry_id: str) -> dict[str, Any]:
        """
        Reload a single integration config entry without restarting HA.

        Triggers HA to unload and re-initialise the integration identified
        by ``entry_id``. Useful for applying config changes or recovering
        a broken integration without a full restart. Obtain ``entry_id``
        from ``list_config_entries``.

        Args:
            entry_id: Config entry ID, e.g. ``"a1b2c3d4e5f6..."``.

        Returns:
            Result object with a ``require_restart`` boolean indicating
            whether a full HA restart is still needed.
        """

        async with client:
            return await client.post(f"/api/config/config_entries/entry/{entry_id}/reload")
