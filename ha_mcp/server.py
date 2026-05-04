"""
Home Assistant MCP server entry point.

Loads configuration from a YAML file or environment variables and registers
all tool modules.

Usage:
    uv run ha-mcp

Configuration (in order of precedence):
    HA_CONFIG: Path to a YAML or JSON config file with multiple instances.
    ha-mcp.yaml: Config file in the current directory (auto-discovered).
    HA_URL + HA_TOKEN: Single-instance fallback via environment variables.

Config file format (ha-mcp.yaml):
    instances:
      - name: home
        url: http://homeassistant.local:8123
        token: <long-lived access token>
      - name: office
        url: http://office-ha.local:8123
        token: <long-lived access token>
    default: home  # optional; defaults to the first instance
"""

from __future__ import annotations

from contextlib import AsyncExitStack, asynccontextmanager
from dataclasses import dataclass
import os
from typing import TYPE_CHECKING, Literal

from mcp.server.fastmcp import FastMCP

from ha_mcp.client import HomeAssistantClient
from ha_mcp.config import load_config
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

_VALID_TRANSPORTS: tuple[Literal["stdio", "sse", "streamable-http"], ...] = (
    "stdio",
    "sse",
    "streamable-http",
)


@dataclass
class AppState:
    """Lifespan state shared across all tool calls."""

    clients: dict[str, HomeAssistantClient]
    default_instance: str


@asynccontextmanager
async def app_lifespan(app: FastMCP) -> AsyncIterator[AppState]:
    """
    Open one persistent HTTP session per configured HA instance.

    Yields an AppState whose clients dict maps instance names to open
    HomeAssistantClient sessions. Tools resolve the target client by
    looking up the instance name passed by the caller.
    """

    config = load_config()
    async with AsyncExitStack() as stack:
        clients: dict[str, HomeAssistantClient] = {}
        for inst in config.instances:
            client = await stack.enter_async_context(
                HomeAssistantClient(base_url=inst.url, token=inst.token)
            )
            clients[inst.name] = client
        yield AppState(clients=clients, default_instance=config.default)


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
    (default 8765). Raises ValueError for any other TRANSPORT value rather than
    silently falling back.
    """

    raw = os.getenv("TRANSPORT", "stdio")
    if raw not in _VALID_TRANSPORTS:
        raise ValueError(
            f"Invalid TRANSPORT {raw!r}. "
            f"Must be one of: {', '.join(_VALID_TRANSPORTS)}."
        )
    transport: Literal["stdio", "sse", "streamable-http"] = raw
    port = int(os.getenv("PORT", "8765"))
    server = create_server(port=port)
    server.run(transport=transport)


if __name__ == "__main__":
    main()
