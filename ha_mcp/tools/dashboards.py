"""MCP tools for Home Assistant Lovelace dashboard management."""

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
            List of dashboard config objects including ``url_path``,
            ``title``, and ``mode``.
        """

        async with client:
            return await client.get("/api/lovelace/dashboards")

    @mcp.tool()
    async def get_dashboard_config(url_path: str | None = None) -> dict[str, Any]:
        """
        Get the full Lovelace YAML/JSON configuration for a dashboard.

        Args:
            url_path: Dashboard URL path, e.g. ``lovelace`` for the default dashboard,
                or ``lovelace-mobile`` for a custom one. Leave ``None`` for the default.

        Returns:
            Full dashboard config dict with ``views``, ``title``, and ``background``.
        """

        params = {"url_path": url_path} if url_path and url_path != "lovelace" else None

        async with client:
            return await client.get("/api/lovelace/config", params=params)

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
            url_path: Unique URL path for the dashboard, e.g. ``my-dashboard``.
            title: Human-readable title shown in the sidebar.
            icon: Optional MDI icon name, e.g. ``mdi:home``.
            show_in_sidebar: Whether to display the dashboard link in the sidebar.
            require_admin: Restrict access to administrator accounts only.

        Returns:
            The created dashboard object.
        """

        payload: dict[str, Any] = {
            "url_path": url_path,
            "title": title,
            "show_in_sidebar": show_in_sidebar,
            "require_admin": require_admin,
        }
        if icon:
            payload["icon"] = icon

        async with client:
            return await client.post("/api/lovelace/dashboards", payload)

    @mcp.tool()
    async def update_dashboard_config(
        config: dict[str, Any],
        url_path: str | None = None,
    ) -> str:
        """
        Replace the full configuration of a Lovelace dashboard.

        Args:
            config: Complete dashboard config dict, must include ``views``.
            url_path: Dashboard URL path to update. ``None`` targets
                the default dashboard.

        Returns:
            Confirmation string from HA.
        """

        path = "/api/lovelace/config"
        if url_path and url_path != "lovelace":
            path = f"/api/lovelace/config?url_path={url_path}"

        async with client:
            return await client.post(path, config)

    @mcp.tool()
    async def delete_dashboard(url_path: str) -> str:
        """
        Delete a Lovelace dashboard by its URL path.

        Args:
            url_path: Dashboard URL path to delete, e.g. ``my-old-dashboard``.

        Returns:
            Confirmation message.
        """

        async with client:
            return await client.delete(f"/api/lovelace/dashboards/{url_path}")
