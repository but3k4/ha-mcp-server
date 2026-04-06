"""Tests for notification tools."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from unittest.mock import MagicMock

import pytest

from ha_mcp.tools import notifications
from tests.conftest import ToolCapture

_SERVICES: list[dict[str, Any]] = [
    {"domain": "notify", "services": {"notify": {}, "mobile_app_my_phone": {}}},
    {"domain": "light", "services": {"turn_on": {}}},
]

_STATES: list[dict[str, Any]] = [
    {
        "entity_id": "persistent_notification.alert1",
        "state": "notifying",
        "attributes": {"message": "Update available", "title": "HA Update"},
    },
    {"entity_id": "light.kitchen", "state": "on", "attributes": {}},
]


@pytest.fixture
def tools(mock_client: MagicMock) -> dict[str, Any]:
    """Register notification tools against a mock client and return the tool dict."""

    capture = ToolCapture()
    notifications.register(capture, mock_client)  # type: ignore[arg-type]
    return capture.tools


async def test_list_notification_services(
    tools: dict[str, Any], mock_client: MagicMock
) -> None:
    """list_notification_services returns only service names under the 'notify' domain."""

    mock_client.get.return_value = _SERVICES
    result = await tools["list_notification_services"]()
    assert "notify" in result
    assert "mobile_app_my_phone" in result
    assert "turn_on" not in result


async def test_list_notification_services_no_notify_domain(
    tools: dict[str, Any], mock_client: MagicMock
) -> None:
    """list_notification_services returns an empty list when no 'notify' domain is present."""

    mock_client.get.return_value = [{"domain": "light", "services": {"turn_on": {}}}]
    result = await tools["list_notification_services"]()
    assert result == []


async def test_send_notification_minimal(
    tools: dict[str, Any], mock_client: MagicMock
) -> None:
    """send_notification posts to notify/notify with only the message when no extras given."""

    mock_client.post.return_value = []
    await tools["send_notification"]("Hello world")
    mock_client.post.assert_called_once_with(
        "/api/services/notify/notify",
        {"message": "Hello world"},
    )


async def test_send_notification_full(
    tools: dict[str, Any], mock_client: MagicMock
) -> None:
    """
    send_notification posts to the specified service with title, target, and
    data fields.
    """

    mock_client.post.return_value = []
    await tools["send_notification"](
        "Motion detected",
        title="Security",
        service="mobile_app_my_phone",
        target=["device/abc123"],
        data={"push": {"sound": "default"}},
    )
    mock_client.post.assert_called_once_with(
        "/api/services/notify/mobile_app_my_phone",
        {
            "message": "Motion detected",
            "title": "Security",
            "target": ["device/abc123"],
            "data": {"push": {"sound": "default"}},
        },
    )


async def test_list_persistent_notifications(
    tools: dict[str, Any], mock_client: MagicMock
) -> None:
    """list_persistent_notifications returns only persistent_notification.* entities."""

    mock_client.get.return_value = _STATES
    result = await tools["list_persistent_notifications"]()
    assert len(result) == 1
    assert result[0]["entity_id"] == "persistent_notification.alert1"


async def test_create_persistent_notification_minimal(
    tools: dict[str, Any], mock_client: MagicMock
) -> None:
    """create_persistent_notification posts with message only when no title or id given."""

    mock_client.post.return_value = []
    await tools["create_persistent_notification"]("Backup complete")
    mock_client.post.assert_called_once_with(
        "/api/services/persistent_notification/create",
        {"message": "Backup complete"},
    )


async def test_create_persistent_notification_full(
    tools: dict[str, Any], mock_client: MagicMock
) -> None:
    """create_persistent_notification includes title and notification_id when provided."""

    mock_client.post.return_value = []
    await tools["create_persistent_notification"](
        "Update ready", title="HA Update", notification_id="ha_update"
    )
    mock_client.post.assert_called_once_with(
        "/api/services/persistent_notification/create",
        {
            "message": "Update ready",
            "title": "HA Update",
            "notification_id": "ha_update",
        },
    )


async def test_dismiss_persistent_notification(
    tools: dict[str, Any], mock_client: MagicMock
) -> None:
    """dismiss_persistent_notification calls the dismiss service with the notification_id."""

    mock_client.post.return_value = []
    await tools["dismiss_persistent_notification"]("ha_update")
    mock_client.post.assert_called_once_with(
        "/api/services/persistent_notification/dismiss",
        {"notification_id": "ha_update"},
    )
