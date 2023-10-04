from django.conf import settings
from apps.accounts.models import User
from apps.common.consumers import BaseConsumer
from apps.common.error import ErrorCode
import json

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

    async def receive(self, notification_obj):
        user = self.scope["user"]
        if user != settings.SOCKET_SECRET:
            await self.send_error_message(
                {
                    "type": ErrorCode.NOT_ALLOWED,
                    "message": "You're not allowed to send data",
                }
            )
            return await self.close(code=1001)

        # Send notification data
        self.scope["notification_obj"] = notification_obj
        notification_data = NotificationSerializer(notification_obj).data
        await self.channel_layer.group_send(
            self.room_group_name,
            {"type": "notification_message", "notification_data": notification_data},
        )

    async def notification_message(self, event):
        notification_data = event["notification_data"]
        user = self.scope["user"]
        notification_obj = self.scope["notification_obj"]

        if isinstance(user, User):
            if await notification_obj.receivers.filter(id=user.id).aexists():
                # Ensure that only receivers of the notification can read it.
                await self.send(text_data=json.dumps(notification_data))