"""
MCP tools for Home Assistant Supervisor add-on management.

These tools require a Supervisor-enabled installation (e.g. Home Assistant OS or Supervised).
They use the Supervisor API at ``/api/hassio/``.
"""
from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from ha_mcp.client import HomeAssistantClient

_SUPERVISOR_PREFIX = "/api/hassio"


def register(mcp: FastMCP, client: HomeAssistantClient) -> None:
    """
    Register all add-on management tools on the MCP server.

    Args:
        mcp: The FastMCP server instance to register tools on.
        client: The authenticated Home Assistant client.
    """

    @mcp.tool()
    async def list_addons() -> list[dict[str, Any]]:
        """List all available and installed Home Assistant add-ons.

        Returns:
            List of add-on summary objects with ``slug``, ``name``, ``state``,
            ``version``, ``version_latest``, and ``update_available``.
        """

        async with client:
            response: dict[str, Any] = await client.get(f"{_SUPERVISOR_PREFIX}/addons")

        return response.get("data", {}).get("addons", [])

    @mcp.tool()
    async def get_addon_info(addon_slug: str) -> dict[str, Any]:
        """
        Get detailed information about a specific add-on.

        Args:
            addon_slug: Add-on slug identifier, e.g. ``core_mosquitto`` or ``a0d7b954_vscode``.

        Returns:
            Detailed add-on info including version, state, options, ports, and ingress config.
        """

        async with client:
            response: dict[str, Any] = await client.get(
                f"{_SUPERVISOR_PREFIX}/addons/{addon_slug}/info"
            )

        return response.get("data", response)

    @mcp.tool()
    async def install_addon(addon_slug: str) -> str:
        """
        Install a Home Assistant add-on from the store.

        Args:
            addon_slug: Add-on slug to install, e.g. ``core_ssh``.

        Returns:
            Confirmation message.
        """

        async with client:
            response: dict[str, Any] = await client.post(
                f"{_SUPERVISOR_PREFIX}/addons/{addon_slug}/install"
            )

        return response.get("result", str(response))

    @mcp.tool()
    async def uninstall_addon(addon_slug: str) -> str:
        """
        Uninstall a Home Assistant add-on.

        Args:
            addon_slug: Add-on slug to remove.

        Returns:
            Confirmation message.
        """

        async with client:
            response: dict[str, Any] = await client.post(
                f"{_SUPERVISOR_PREFIX}/addons/{addon_slug}/uninstall"
            )

        return response.get("result", str(response))

    @mcp.tool()
    async def update_addon(addon_slug: str) -> str:
        """
        Update a Home Assistant add-on to the latest available version.

        Args:
            addon_slug: Add-on slug to update.

        Returns:
            Confirmation message.
        """

        async with client:
            response: dict[str, Any] = await client.post(
                f"{_SUPERVISOR_PREFIX}/addons/{addon_slug}/update"
            )

        return response.get("result", str(response))

    @mcp.tool()
    async def start_addon(addon_slug: str) -> str:
        """
        Start a stopped Home Assistant add-on.

        Args:
            addon_slug: Add-on slug to start.

        Returns:
            Confirmation message.
        """

        async with client:
            response: dict[str, Any] = await client.post(
                f"{_SUPERVISOR_PREFIX}/addons/{addon_slug}/start"
            )

        return response.get("result", str(response))

    @mcp.tool()
    async def stop_addon(addon_slug: str) -> str:
        """
        Stop a running Home Assistant add-on.

        Args:
            addon_slug: Add-on slug to stop.

        Returns:
            Confirmation message.
        """

        async with client:
            response: dict[str, Any] = await client.post(
                f"{_SUPERVISOR_PREFIX}/addons/{addon_slug}/stop"
            )

        return response.get("result", str(response))

    @mcp.tool()
    async def restart_addon(addon_slug: str) -> str:
        """
        Restart a Home Assistant add-on.

        Args:
            addon_slug: Add-on slug to restart.

        Returns:
            Confirmation message.
        """

        async with client:
            response: dict[str, Any] = await client.post(
                f"{_SUPERVISOR_PREFIX}/addons/{addon_slug}/restart"
            )

        return response.get("result", str(response))

    @mcp.tool()
    async def get_addon_logs(addon_slug: str) -> str:
        """
        Fetch the stdout/stderr logs for a specific add-on.

        Args:
            addon_slug: Add-on slug whose logs to retrieve.

        Returns:
            Raw log output as a string.
        """

        async with client:
            return await client.get(f"{_SUPERVISOR_PREFIX}/addons/{addon_slug}/logs")

    @mcp.tool()
    async def set_addon_options(addon_slug: str, options: dict[str, Any]) -> str:
        """
        Update configuration options for a Home Assistant add-on.

        Args:
            addon_slug: Add-on slug to configure.
            options: Dictionary of option keys and values specific to the add-on.

        Returns:
            Confirmation message.
        """

        async with client:
            response: dict[str, Any] = await client.post(
                f"{_SUPERVISOR_PREFIX}/addons/{addon_slug}/options",
                {"options": options},
            )

        return response.get("result", str(response))

    @mcp.tool()
    async def list_addon_repositories() -> list[dict[str, Any]]:
        """
        List all configured add-on repositories (stores).

        Returns:
            List of repository objects with ``slug``, ``name``, ``source``, and ``maintainer``.
        """

        async with client:
            response: dict[str, Any] = await client.get(f"{_SUPERVISOR_PREFIX}/store/repositories")

        return response.get("data", {}).get("repositories", [])

    @mcp.tool()
    async def add_addon_repository(repository_url: str) -> str:
        """
        Add a third-party add-on repository to Home Assistant.

        Args:
            repository_url: Git URL of the repository, e.g. ``https://github.com/owner/repo``.

        Returns:
            Confirmation message.
        """

        async with client:
            response: dict[str, Any] = await client.post(
                f"{_SUPERVISOR_PREFIX}/store/repositories",
                {"repository": repository_url},
            )

        return response.get("result", str(response))
