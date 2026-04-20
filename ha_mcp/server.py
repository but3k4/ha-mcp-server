"""
Home Assistant MCP server entry point.

Loads configuration from environment variables and registers all tool modules.

Usage:
    uv run ha-mcp

Environment Variables:
    HA_URL:   Base URL of the Home Assistant instance, e.g.
              http://homeassistant.local:8123.
    HA_TOKEN: Long-lived access token from your HA profile.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from dataclasses import dataclass
import os
from pathlib import Path
from typing import TYPE_CHECKING, Literal

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

if TYPE_CHECKING:
    from collections.abc import AsyncIterator


@dataclass
class AppState:
    """Lifespan state shared across all tool calls."""

    client: HomeAssistantClient


def _load_client() -> HomeAssistantClient:
    """
    Load HA connection settings from the environment and return a configured client.

    Returns:
        A HomeAssistantClient ready for use. Call it as a context manager to
        open the connection.

    Raises:
        ValueError: If HA_URL or HA_TOKEN are not set in the environment.
    """

    load_dotenv(Path(__file__).parent.parent / ".env")

    ha_url = os.getenv("HA_URL")
    ha_token = os.getenv("HA_TOKEN")

    if not ha_url:
        raise ValueError("HA_URL environment variable is required.")
    if not ha_token:
        raise ValueError("HA_TOKEN environment variable is required.")

    return HomeAssistantClient(base_url=ha_url, token=ha_token)


@asynccontextmanager
async def app_lifespan(app: FastMCP) -> AsyncIterator[AppState]:
    """
    Open a single persistent HTTP session for the server's lifetime.

    Yields an :class: AppState whose client is already entered (session open).
    Tools access it via ctx.request_context.lifespan_context.client.
    """

    client = _load_client()
    async with client as c:
        yield AppState(client=c)


def create_server(port: int = 8000) -> FastMCP:
    """
    Create and configure the FastMCP server with all Home Assistant tools registered.

    Args:
        port: TCP port for SSE transport. Ignored in stdio mode.

    Returns:
        Configured FastMCP server instance.
    """

    mcp = FastMCP(
        name="home-assistant",
        host="0.0.0.0",
        port=port,
        lifespan=app_lifespan,
        instructions=(
            "You are connected to a Home Assistant instance. "
            "You can control smart home devices, manage automations, "
            "dashboards, add-ons, view logs, check system health, "
            "send notifications, manage input helpers and timers, "
            "and inspect the device and integration registries. "
            "Use call_service for controlling physical devices. "
            "Use set_entity_state only for virtual/input entities. "
            "Use the dedicated set_input_* tools for input helpers "
            "instead of call_service. "
            "Supervisor tools (add-ons, updates, backups) require "
            "HA OS or Supervised installation."
        ),
    )

    entities.register(mcp)
    dashboards.register(mcp)
    addons.register(mcp)
    logs.register(mcp)
    automations.register(mcp)
    system.register(mcp)
    notifications.register(mcp)
    helpers.register(mcp)
    registry.register(mcp)

    return mcp


def main() -> None:
    """
    Run the Home Assistant MCP server.

    Reads the TRANSPORT environment variable to select the transport. Defaults
    to stdio. When set to sse, binds an HTTP server on the port given by PORT
    (default 8765).
    """

    raw = os.getenv("TRANSPORT", "stdio")
    transport: Literal["stdio", "sse", "streamable-http"] = (
        raw if raw in ("stdio", "sse", "streamable-http") else "stdio"  # type: ignore[assignment]
    )
    port = int(os.getenv("PORT", "8765"))
    server = create_server(port=port)
    server.run(transport=transport)


if __name__ == "__main__":
    main()
