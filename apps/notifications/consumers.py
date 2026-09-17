import json

from channels.generic.websocket import AsyncJsonWebsocketConsumer


class NotificationConsumer(AsyncJsonWebsocketConsumer):
    """
    ws://host/ws/notifications/
    Auth: the browser's Django session cookie, resolved by Channels'
    AuthMiddlewareStack (see config/asgi.py) onto scope["user"] — the same
    session used for every other page on the site.
    Each connected user joins a private group `user_<id>_notifications`,
    so pushes from notifications.services.notify_user() land here in real time.
    """

    async def connect(self):
        user = self.scope.get("user")
        if user is None or not user.is_authenticated:
            await self.close(code=4001)
            return

        self.group_name = f"user_{user.id}_notifications"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        await self.send_json({"type": "connection_established"})

    async def disconnect(self, close_code):
        group_name = getattr(self, "group_name", None)
        if group_name:
            await self.channel_layer.group_discard(group_name, self.channel_name)

    async def receive_json(self, content, **kwargs):
        # Client can ping to keep the connection alive; no other inbound
        # commands are expected — this channel is push-only from the server.
        if content.get("action") == "ping":
            await self.send_json({"type": "pong"})

    async def notification_message(self, event):
        """Handler for the `notification.message` group_send type."""
        await self.send_json({"type": "notification", "payload": event["payload"]})
