"""
Single entry point for creating + delivering a notification.
Called from anywhere in the codebase (signal handlers, views, celery tasks)
instead of touching Notification.objects.create() directly, so delivery
(DB row + WebSocket push) always stays in sync.
"""

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from .models import Notification


def _serialize(notification):
    return {
        "id": notification.id,
        "title": notification.title,
        "message": notification.message,
        "type": notification.type,
        "data": notification.data,
        "is_read": notification.is_read,
        "created_at": notification.created_at.isoformat(),
    }


def notify_user(user, title, message, notif_type, extra=None):
    if user is None:
        return None

    notification = Notification.objects.create(
        user=user,
        title=title,
        message=message,
        type=notif_type,
        data=extra or {},
    )

    _push_to_websocket(notification)
    return notification


def _push_to_websocket(notification):
    channel_layer = get_channel_layer()
    if channel_layer is None:
        return
    group_name = f"user_{notification.user_id}_notifications"
    async_to_sync(channel_layer.group_send)(
        group_name,
        {
            "type": "notification.message",
            "payload": _serialize(notification),
        },
    )
