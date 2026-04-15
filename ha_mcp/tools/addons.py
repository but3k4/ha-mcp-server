"""
MCP tools for Home Assistant Supervisor add-on management.

These tools require a Supervisor-enabled installation
(e.g. Home Assistant OS or Supervised).
They use the Supervisor API at ``/api/hassio/``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from mcp.server.fastmcp import Context
from mcp.types import ToolAnnotations

from ha_mcp.client import HomeAssistantError

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

    from ha_mcp.client import HomeAssistantClient

_SUPERVISOR_PREFIX = "/api/hassio"


def register(mcp: FastMCP) -> None:
    """Register all add-on management tools on the MCP server."""

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=True))
    async def list_addons(ctx: Context) -> list[dict[str, Any]] | str:
        """
        List all available and installed Home Assistant add-ons.

        Requires a Supervisor-enabled installation (HA OS or Supervised).
        Use ``get_addon_info`` to retrieve full details for a specific add-on, or
        ``set_addon_options`` to configure one.

        Args:
            ctx: MCP request context (injected by FastMCP).

        Returns:
            List of add-on summary objects with ``slug``, ``name``, ``state``,
            ``version``, ``version_latest``, and ``update_available``.
        """

        client: HomeAssistantClient = ctx.request_context.lifespan_context.client
        try:
            response: dict[str, Any] = await client.get(f"{_SUPERVISOR_PREFIX}/addons")
        except HomeAssistantError as exc:
            return f"Error: {exc}"
        return response.get("data", {}).get("addons", [])

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=True))
    async def get_addon_info(ctx: Context, addon_slug: str) -> dict[str, Any] | str:
        """
        Get detailed information about a specific add-on.

        Requires a Supervisor-enabled installation (HA OS or Supervised).
        Use ``get_addon_logs`` to inspect runtime output, or ``set_addon_options``
        to change configuration.

        Args:
            ctx: MCP request context (injected by FastMCP).
            addon_slug: Add-on slug identifier, e.g. ``core_mosquitto``
                or ``a0d7b954_vscode``.

        Returns:
            Detailed add-on info including version, state, options,
            ports, and ingress config.
        """

        client: HomeAssistantClient = ctx.request_context.lifespan_context.client
        try:
            response: dict[str, Any] = await client.get(
                f"{_SUPERVISOR_PREFIX}/addons/{addon_slug}/info"
            )
        except HomeAssistantError as exc:
            return f"Error: {exc}"
        return response.get("data", response)

    @mcp.tool(annotations=ToolAnnotations(openWorldHint=True))
    async def install_addon(ctx: Context, addon_slug: str) -> str:
        """
        Install a Home Assistant add-on from the store.

        Requires a Supervisor-enabled installation (HA OS or Supervised).

        Args:
            ctx: MCP request context (injected by FastMCP).
            addon_slug: Add-on slug to install, e.g. ``core_ssh``.

        Returns:
            Confirmation message.
        """

        client: HomeAssistantClient = ctx.request_context.lifespan_context.client
        try:
            response: dict[str, Any] = await client.post(
                f"{_SUPERVISOR_PREFIX}/addons/{addon_slug}/install"
            )
        except HomeAssistantError as exc:
            return f"Error: {exc}"
        return response.get("result", str(response))

    @mcp.tool(annotations=ToolAnnotations(destructiveHint=True, openWorldHint=True))
    async def uninstall_addon(ctx: Context, addon_slug: str) -> str:
        """
        Uninstall a Home Assistant add-on. This action is irreversible.

        Requires a Supervisor-enabled installation (HA OS or Supervised).

        Args:
            ctx: MCP request context (injected by FastMCP).
            addon_slug: Add-on slug to remove.

        Returns:
            Confirmation message.
        """

        client: HomeAssistantClient = ctx.request_context.lifespan_context.client
        try:
            response: dict[str, Any] = await client.post(
                f"{_SUPERVISOR_PREFIX}/addons/{addon_slug}/uninstall"
            )
        except HomeAssistantError as exc:
            return f"Error: {exc}"
        return response.get("result", str(response))

    @mcp.tool(annotations=ToolAnnotations(openWorldHint=True))
    async def update_addon(ctx: Context, addon_slug: str) -> str:
        """
        Update a Home Assistant add-on to the latest available version.

        Requires a Supervisor-enabled installation (HA OS or Supervised).

        Args:
            ctx: MCP request context (injected by FastMCP).
            addon_slug: Add-on slug to update.

        Returns:
            Confirmation message.
        """

        client: HomeAssistantClient = ctx.request_context.lifespan_context.client
        try:
            response: dict[str, Any] = await client.post(
                f"{_SUPERVISOR_PREFIX}/addons/{addon_slug}/update"
            )
        except HomeAssistantError as exc:
            return f"Error: {exc}"
        return response.get("result", str(response))

    @mcp.tool(annotations=ToolAnnotations(openWorldHint=True))
    async def start_addon(ctx: Context, addon_slug: str) -> str:
        """
        Start a stopped Home Assistant add-on.

        Requires a Supervisor-enabled installation (HA OS or Supervised).

        Args:
            ctx: MCP request context (injected by FastMCP).
            addon_slug: Add-on slug to start.

        Returns:
            Confirmation message.
        """

        client: HomeAssistantClient = ctx.request_context.lifespan_context.client
        try:
            response: dict[str, Any] = await client.post(
                f"{_SUPERVISOR_PREFIX}/addons/{addon_slug}/start"
            )
        except HomeAssistantError as exc:
            return f"Error: {exc}"
        return response.get("result", str(response))

    @mcp.tool(annotations=ToolAnnotations(openWorldHint=True))
    async def stop_addon(ctx: Context, addon_slug: str) -> str:
        """
        Stop a running Home Assistant add-on.

        Requires a Supervisor-enabled installation (HA OS or Supervised).

        Args:
            ctx: MCP request context (injected by FastMCP).
            addon_slug: Add-on slug to stop.

        Returns:
            Confirmation message.
        """

        client: HomeAssistantClient = ctx.request_context.lifespan_context.client
        try:
            response: dict[str, Any] = await client.post(
                f"{_SUPERVISOR_PREFIX}/addons/{addon_slug}/stop"
            )
        except HomeAssistantError as exc:
            return f"Error: {exc}"
        return response.get("result", str(response))

    @mcp.tool(annotations=ToolAnnotations(openWorldHint=True))
    async def restart_addon(ctx: Context, addon_slug: str) -> str:
        """
        Restart a Home Assistant add-on.

        Requires a Supervisor-enabled installation (HA OS or Supervised).

        Args:
            ctx: MCP request context (injected by FastMCP).
            addon_slug: Add-on slug to restart.

        Returns:
            Confirmation message.
        """

        client: HomeAssistantClient = ctx.request_context.lifespan_context.client
        try:
            response: dict[str, Any] = await client.post(
                f"{_SUPERVISOR_PREFIX}/addons/{addon_slug}/restart"
            )
        except HomeAssistantError as exc:
            return f"Error: {exc}"
        return response.get("result", str(response))

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=True))
    async def get_addon_logs(ctx: Context, addon_slug: str) -> str:
        """
        Fetch the stdout/stderr logs for a specific add-on.

        Requires a Supervisor-enabled installation (HA OS or Supervised).
        Returns an empty string if the add-on has never started or has no
        log output.

        Args:
            ctx: MCP request context (injected by FastMCP).
            addon_slug: Add-on slug whose logs to retrieve.

        Returns:
            Raw log output as a string.
        """

        client: HomeAssistantClient = ctx.request_context.lifespan_context.client
        try:
            return await client.get(f"{_SUPERVISOR_PREFIX}/addons/{addon_slug}/logs")
        except HomeAssistantError as exc:
            return f"Error: {exc}"

    @mcp.tool(annotations=ToolAnnotations(openWorldHint=True))
    async def set_addon_options(
        ctx: Context, addon_slug: str, options: dict[str, Any]
    ) -> str:
        """
        Update configuration options for a Home Assistant add-on.

        Requires a Supervisor-enabled installation (HA OS or Supervised).
        The add-on must be restarted after updating options for changes to take
        effect. Use ``get_addon_info`` to inspect the current ``options`` schema.

        Args:
            ctx: MCP request context (injected by FastMCP).
            addon_slug: Add-on slug to configure.
            options: Dictionary of option keys and values specific to the add-on.

        Returns:
            Confirmation message.
        """

        client: HomeAssistantClient = ctx.request_context.lifespan_context.client
        try:
            response: dict[str, Any] = await client.post(
                f"{_SUPERVISOR_PREFIX}/addons/{addon_slug}/options",
                {"options": options},
            )
        except HomeAssistantError as exc:
            return f"Error: {exc}"
        return response.get("result", str(response))

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=True))
    async def list_addon_repositories(ctx: Context) -> list[dict[str, Any]] | str:
        """
        List all configured add-on repositories (stores).

        Requires a Supervisor-enabled installation (HA OS or Supervised).

        Args:
            ctx: MCP request context (injected by FastMCP).

        Returns:
            List of repository objects with ``slug``, ``name``,
            ``source``, and ``maintainer``.
        """

        client: HomeAssistantClient = ctx.request_context.lifespan_context.client
        try:
            response: dict[str, Any] = await client.get(
                f"{_SUPERVISOR_PREFIX}/store/repositories"
            )
        except HomeAssistantError as exc:
            return f"Error: {exc}"
        return response.get("data", {}).get("repositories", [])

    @mcp.tool(annotations=ToolAnnotations(openWorldHint=True))
    async def add_addon_repository(ctx: Context, repository_url: str) -> str:
        """
        Add a third-party add-on repository to Home Assistant.

        Requires a Supervisor-enabled installation (HA OS or Supervised).

        Args:
            ctx: MCP request context (injected by FastMCP).
            repository_url: Git URL of the repository,
                e.g. ``https://github.com/owner/repo``.

        Returns:
            Confirmation message.
        """

        client: HomeAssistantClient = ctx.request_context.lifespan_context.client
        try:
            response: dict[str, Any] = await client.post(
                f"{_SUPERVISOR_PREFIX}/store/repositories",
                {"repository": repository_url},
            )
        except HomeAssistantError as exc:
            return f"Error: {exc}"
        return response.get("result", str(response))
