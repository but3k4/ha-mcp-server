"""MCP tools for Home Assistant Lovelace dashboard management.

All tools use the HA WebSocket API (``/api/websocket``) instead of the
REST endpoints, because the REST Lovelace API is unavailable when HA is
configured in YAML mode.  The WebSocket API works in both storage and
YAML mode.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

    from ha_mcp.client import HomeAssistantClient


def register(mcp: FastMCP, client: HomeAssistantClient) -> None:
    """
    Register all Lovelace dashboard tools on the MCP server.

    Args:
        mcp: The FastMCP server instance to register tools on.
        client: The authenticated Home Assistant client.
    """

    @mcp.tool()
    async def list_dashboards() -> list[dict[str, Any]]:
        """
        List all Lovelace dashboards configured in Home Assistant.

        Returns:
            List of dashboard objects, each containing ``url_path``,
            ``title``, ``mode``, and sidebar visibility flags.
        """
        result = await client.ws_command("lovelace/dashboards/list")
        return result  # type: ignore[return-value]

    @mcp.tool()
    async def get_dashboard_config(url_path: str | None = None) -> dict[str, Any]:
        """
        Get the full Lovelace configuration for a dashboard.

        Args:
            url_path: Dashboard URL path, e.g. ``kiosk`` for a dashboard
                accessible at ``/dashboard-kiosk/``.  Leave ``None`` or
                pass ``"lovelace"`` to target the default dashboard.

        Returns:
            Full dashboard config dict containing ``views`` and optional
            ``title`` and ``background`` fields.
        """
        kwargs: dict[str, Any] = {}
        if url_path and url_path != "lovelace":
            kwargs["url_path"] = url_path
        result = await client.ws_command("lovelace/config", **kwargs)
        return result  # type: ignore[return-value]

    @mcp.tool()
    async def create_dashboard(
        url_path: str,
        title: str,
        icon: str | None = None,
        show_in_sidebar: bool = True,
        require_admin: bool = False,
    ) -> dict[str, Any]:
        """
        Create a new Lovelace dashboard.

        Args:
            url_path: Unique URL path for the dashboard.  HA will expose
                it at ``/dashboard-{url_path}/``, e.g. ``tablet`` becomes
                ``/dashboard-tablet/``.
            title: Human-readable title shown in the sidebar.
            icon: Optional MDI icon name, e.g. ``mdi:tablet``.
            show_in_sidebar: Whether to display the dashboard link in the
                sidebar.  Defaults to ``True``.
            require_admin: Restrict access to administrator accounts only.
                Defaults to ``False``.

        Returns:
            The created dashboard object returned by HA.
        """
        kwargs: dict[str, Any] = {
            "url_path": url_path,
            "title": title,
            "show_in_sidebar": show_in_sidebar,
            "require_admin": require_admin,
        }
        if icon:
            kwargs["icon"] = icon
        result = await client.ws_command("lovelace/dashboards/create", **kwargs)
        return result  # type: ignore[return-value]

    @mcp.tool()
    async def update_dashboard_config(
        config: dict[str, Any],
        url_path: str | None = None,
    ) -> str:
        """
        Replace the full configuration of a Lovelace dashboard.

        Args:
            config: Complete dashboard config dict, must include ``views``.
            url_path: Dashboard URL path to update.  ``None`` or
                ``"lovelace"`` targets the default dashboard.

        Returns:
            Confirmation string.
        """
        kwargs: dict[str, Any] = {"config": config}
        if url_path and url_path != "lovelace":
            kwargs["url_path"] = url_path
        await client.ws_command("lovelace/config/save", **kwargs)
        return "Dashboard configuration saved."

    @mcp.tool()
    async def update_dashboard(
        dashboard_id: str,
        title: str | None = None,
        url_path: str | None = None,
        icon: str | None = None,
        show_in_sidebar: bool | None = None,
        require_admin: bool | None = None,
    ) -> str:
        """
        Update metadata for an existing Lovelace dashboard.

        Args:
            dashboard_id: Internal dashboard ID as returned by ``list_dashboards``
                (the ``id`` field, not ``url_path``), e.g. ``dashboard_ios``.
            title: New display title.
            url_path: New URL slug, e.g. ``dashboard-tablet``.
            icon: MDI icon string, e.g. ``mdi:tablet``.
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
        await client.ws_command(
            "lovelace/dashboards/update", dashboard_id=dashboard_id, **kwargs
        )
        return f"Dashboard {dashboard_id!r} updated."

    @mcp.tool()
    async def delete_dashboard(dashboard_id: str) -> str:
        """
        Delete a Lovelace dashboard by its ID.

        Args:
            dashboard_id: The internal dashboard ID as returned by
                ``list_dashboards``, e.g. ``dashboard_tablet``.  Note that
                this is the ``id`` field, not the ``url_path``.

        Returns:
            Confirmation string.
        """
        await client.ws_command("lovelace/dashboards/delete", dashboard_id=dashboard_id)
        return f"Dashboard {dashboard_id!r} deleted."
