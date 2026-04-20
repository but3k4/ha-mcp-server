"""Shared test fixtures and helpers."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from ha_mcp.client import HomeAssistantClient

if TYPE_CHECKING:
    from collections.abc import Callable


class ToolCapture:
    """Minimal MCP stub that captures @mcp.tool()-decorated functions by name."""

    def __init__(self) -> None:
        self.tools: dict[str, Callable[..., Any]] = {}

    def tool(
        self, **_kwargs: Any
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """
        Return a decorator that stores the decorated function by name.

        Mirrors the @mcp.tool() interface so that register(capture) calls
        populate self.tools with the raw async functions, making them directly
        callable in tests without a live MCP server. Keyword arguments (e.g.
        readOnlyHint, destructiveHint) are accepted and ignored.
        """

        def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
            self.tools[fn.__name__] = fn
            return fn

        return decorator


@pytest.fixture
def mock_client() -> MagicMock:
    """
    Return a HomeAssistantClient mock with async methods pre-wired.

    get, post, delete, and ws_command are AsyncMock instances. Configure return
    values in each test via mock_client.get.return_value etc.
    """

    client = MagicMock(spec=HomeAssistantClient)
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=None)
    client.get = AsyncMock()
    client.post = AsyncMock()
    client.delete = AsyncMock()
    client.ws_command = AsyncMock()
    return client


@pytest.fixture
def mock_ctx(mock_client: MagicMock) -> MagicMock:
    """
    Return a mock MCP Context with lifespan state pre-wired.

    ctx.request_context.lifespan_context.client resolves to the mock_client
    fixture, matching the structure that tool functions expect when they
    retrieve the client via: ctx.request_context.lifespan_context.client.
    """

    ctx = MagicMock()
    ctx.request_context.lifespan_context.client = mock_client
    return ctx
