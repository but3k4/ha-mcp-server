"""
MCP tools for Home Assistant Lovelace dashboard management.

All tools use the HA WebSocket API (/api/websocket). The Lovelace dashboard API
is not available over REST in YAML-mode installations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from mcp.server.fastmcp import Context
from mcp.types import ToolAnnotations

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

    from ha_mcp.client import HomeAssistantClient


def register(mcp: FastMCP) -> None:
    """Register all Lovelace dashboard tools on the MCP server."""

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=True))
    async def list_dashboards(ctx: Context) -> list[dict[str, Any]]:
        """
        List all Lovelace dashboards configured in Home Assistant.

        Uses the Lovelace WebSocket API.

        Args:
            ctx: MCP request context (injected by FastMCP).

        Returns:
            List of dashboard objects, each containing url_path,
            title, mode, and sidebar visibility flags.
        """

        client: HomeAssistantClient = ctx.request_context.lifespan_context.client
        return await client.ws_command("lovelace/dashboards/list")

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=True))
    async def get_dashboard_config(
        ctx: Context,
        url_path: str | None = None
    ) -> dict[str, Any]:
        """
        Get the full Lovelace configuration for a dashboard.

        Uses the Lovelace WebSocket API.

        Args:
            ctx: MCP request context (injected by FastMCP).
            url_path: Dashboard URL path, e.g. kiosk for a dashboard accessible
                      at /dashboard-kiosk/. Leave None or pass "lovelace" to
                      target the default dashboard.

        Returns:
            Full dashboard config dict containing views and optional title and
            background fields.
        """

        client: HomeAssistantClient = ctx.request_context.lifespan_context.client
        kwargs: dict[str, Any] = {}
        if url_path and url_path != "lovelace":
            kwargs["url_path"] = url_path
        return await client.ws_command("lovelace/config", **kwargs)

    @mcp.tool(annotations=ToolAnnotations(openWorldHint=True))
    async def create_dashboard(
        ctx: Context,
        url_path: str,
        title: str,
        icon: str | None = None,
        show_in_sidebar: bool = True,
        require_admin: bool = False,
    ) -> dict[str, Any]:
        """
        Create a new Lovelace dashboard.

        Uses the Lovelace WebSocket API.

        Args:
            ctx: MCP request context (injected by FastMCP).
            url_path: Unique URL path for the dashboard. HA will expose it at
                      /dashboard-{url_path}/, e.g. tablet becomes
                      /dashboard-tablet/.
            title: Human-readable title shown in the sidebar.
            icon: Optional MDI icon name, e.g. mdi:tablet.
            show_in_sidebar: Whether to display the dashboard link in the
                             sidebar. Defaults to True.
            require_admin: Restrict access to administrator accounts only.
                           Defaults to False.

        Returns:
            The created dashboard object returned by HA.
        """

        client: HomeAssistantClient = ctx.request_context.lifespan_context.client
        kwargs: dict[str, Any] = {
            "url_path": url_path,
            "title": title,
            "show_in_sidebar": show_in_sidebar,
            "require_admin": require_admin,
        }
        if icon:
            kwargs["icon"] = icon
        return await client.ws_command("lovelace/dashboards/create", **kwargs)

    @mcp.tool(annotations=ToolAnnotations(openWorldHint=True))
    async def update_dashboard_config(
        ctx: Context,
        config: dict[str, Any],
        url_path: str | None = None,
    ) -> str:
        """
        Replace the full configuration of a Lovelace dashboard.

        Uses the Lovelace WebSocket API.

        Args:
            ctx: MCP request context (injected by FastMCP).
            config: Complete dashboard config dict, must include views.
            url_path: Dashboard URL path to update. None or "lovelace" targets
                      the default dashboard.

        Returns:
            Confirmation string.
        """

        client: HomeAssistantClient = ctx.request_context.lifespan_context.client
        kwargs: dict[str, Any] = {"config": config}
        if url_path and url_path != "lovelace":
            kwargs["url_path"] = url_path
        await client.ws_command("lovelace/config/save", **kwargs)
        return "Dashboard configuration saved."

    @mcp.tool(annotations=ToolAnnotations(openWorldHint=True))
    async def update_dashboard(
        ctx: Context,
        dashboard_id: str,
        title: str | None = None,
        url_path: str | None = None,
        icon: str | None = None,
        show_in_sidebar: bool | None = None,
        require_admin: bool | None = None,
    ) -> str:
        """
        Update metadata for an existing Lovelace dashboard.

        Uses the Lovelace WebSocket API.

        Args:
            ctx: MCP request context (injected by FastMCP).
            dashboard_id: Internal dashboard ID as returned by list_dashboards
                          (the id field, not url_path), e.g. dashboard_ios.
            title: New display title.
            url_path: New URL slug, e.g. dashboard-tablet.
            icon: MDI icon string, e.g. mdi:tablet.
            show_in_sidebar: Whether the dashboard appears in the sidebar.
            require_admin: Whether the dashboard requires admin access.

        Returns:
            Confirmation string with the updated dashboard ID.
        """

        kwargs: dict[str, object] = {}
        if title is not None:
            kwargs["title"] = title
        if url_path is not None:
            kwargs["url_path"] = url_path
        if icon is not None:
            kwargs["icon"] = icon
        if show_in_sidebar is not None:
            kwargs["show_in_sidebar"] = show_in_sidebar
        if require_admin is not None:
            kwargs["require_admin"] = require_admin
        if not kwargs:
            raise ValueError("At least one field must be provided to update a dashboard.")

        client: HomeAssistantClient = ctx.request_context.lifespan_context.client
        await client.ws_command(
            "lovelace/dashboards/update", dashboard_id=dashboard_id, **kwargs
        )
        return f"Dashboard {dashboard_id!r} updated."

    @mcp.tool(annotations=ToolAnnotations(destructiveHint=True, openWorldHint=True))
    async def delete_dashboard(ctx: Context, dashboard_id: str) -> str:
        """
        Delete a Lovelace dashboard by its ID. This action is irreversible.

        Uses the Lovelace WebSocket API.

        Args:
            ctx: MCP request context (injected by FastMCP).
            dashboard_id: The internal dashboard ID as returned by
                          list_dashboards, e.g. dashboard_tablet. Note that
                          this is the id field, not the url_path.

        Returns:
            Confirmation string.
        """

        client: HomeAssistantClient = ctx.request_context.lifespan_context.client
        await client.ws_command(
            "lovelace/dashboards/delete", dashboard_id=dashboard_id
        )
        return f"Dashboard {dashboard_id!r} deleted."
