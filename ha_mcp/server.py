"""
Home Assistant MCP server entry point.

Loads configuration from environment variables and registers all tool modules.

Usage:
    uv run ha-mcp

Environment Variables:
    HA_URL:   Base URL of the Home Assistant instance, e.g. ``http://homeassistant.local:8123``.
    HA_TOKEN: Long-lived access token from your HA profile.
"""

from __future__ import annotations

import os

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

from ha_mcp.client import HomeAssistantClient
from ha_mcp.tools import (
    addons,
    automations,
    dashboards,
    entities,
    helpers,
    logs,
    notifications,
    registry,
    system,
)


def _load_client() -> HomeAssistantClient:
    """
    Load HA connection settings from the environment and return a configured client.

    Returns:
        A HomeAssistantClient ready for use. Call it as a context manager to open the connection.

    Raises:
        ValueError: If ``HA_URL`` or ``HA_TOKEN`` are not set in the environment.
    """

    load_dotenv()

    ha_url = os.getenv("HA_URL")
    ha_token = os.getenv("HA_TOKEN")

    if not ha_url:
        raise ValueError("HA_URL environment variable is required.")
    if not ha_token:
        raise ValueError("HA_TOKEN environment variable is required.")

    return HomeAssistantClient(base_url=ha_url, token=ha_token)


def create_server() -> FastMCP:
    """
    Create and configure the FastMCP server with all Home Assistant tools registered.

    Returns:
        Configured FastMCP server instance.
    """

    client = _load_client()
    mcp = FastMCP(
        name="home-assistant",
        instructions=(
            "You are connected to a Home Assistant instance. "
            "You can control smart home devices, manage automations, dashboards, add-ons, "
            "view logs, check system health, send notifications, manage input helpers and timers, "
            "and inspect the device and integration registries. "
            "Use call_service for controlling physical devices. "
            "Use set_entity_state only for virtual/input entities. "
            "Use the dedicated set_input_* tools for input helpers instead of call_service. "
            "Supervisor tools (add-ons, updates, backups) require HA OS or Supervised installation."
        ),
    )

    entities.register(mcp, client)
    dashboards.register(mcp, client)
    addons.register(mcp, client)
    logs.register(mcp, client)
    automations.register(mcp, client)
    system.register(mcp, client)
    notifications.register(mcp, client)
    helpers.register(mcp, client)
    registry.register(mcp, client)

    return mcp


def main() -> None:
    """Run the Home Assistant MCP server via stdio transport."""

    server = create_server()
    server.run(transport="stdio")


if __name__ == "__main__":
    main()
