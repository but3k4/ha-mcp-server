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

    def tool(self) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """
        Return a decorator that stores the decorated function by name.

        Mirrors the ``@mcp.tool()`` interface so that ``register(capture,
        client)`` calls populate ``self.tools`` with the raw async functions,
        making them directly callable in tests without a live MCP server.
        """

        def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
            self.tools[fn.__name__] = fn
            return fn

        return decorator


@pytest.fixture
def mock_client() -> MagicMock:
    """
    Return a HomeAssistantClient mock with async context manager pre-wired.

    ``__aenter__`` returns the mock itself so that ``async with client:``
    inside tool functions resolves to the same object whose ``get``,
    ``post``, and ``delete`` methods can be configured via
    ``mock_client.get.return_value`` in each test.
    """
    client = MagicMock(spec=HomeAssistantClient)
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=None)
    client.get = AsyncMock()
    client.post = AsyncMock()
    client.delete = AsyncMock()
    return client
