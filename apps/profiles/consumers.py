from django.conf import settings
from apps.accounts.models import User
from apps.common.consumers import BaseConsumer
from apps.common.error import ErrorCode
import json
from apps.profiles.models import Notification

from apps.profiles.serializers import NotificationSerializer


class NotificationConsumer(BaseConsumer):
    async def connect(self):
        err = self.scope["error"]
        await self.accept()

        if err.get("message"):  # Check for auth errors
            await self.send_error_message(err)
            return await self.close(code=4001)
        self.room_name = "notifications"
        self.room_group_name = "notifications"
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        user = self.scope["user"]
        if user != settings.SOCKET_SECRET:
            await self.send_error_message(
                {
                    "type": ErrorCode.NOT_ALLOWED,
                    "message": "You're not allowed to send data",
                }
            )
            return await self.close(code=1001)

        data = json.loads(text_data)

        # Send notification data
        await self.channel_layer.group_send(
            self.room_group_name,
            {"type": "notification_message", "notification_data": data},
        )

    async def notification_message(self, event):
        notification_data = event["notification_data"]
        user = self.scope["user"]
        if isinstance(user, User):
            if await user.notifications.filter(id=notification_data["id"]).aexists():
                # Ensure that only receivers of the notification can read it.
                await self.send(text_data=json.dumps(notification_data))
