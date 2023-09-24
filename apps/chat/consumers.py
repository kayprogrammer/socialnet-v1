from channels.generic.websocket import AsyncWebsocketConsumer
import json

from django.conf import settings


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        id = self.scope["url_route"]["kwargs"][
            "id"
        ]  # ID is either the chat id or recipient id if its the first message of a dm
        self.room_name = f"chat_{id}"
        self.room_group_name = f"chat_{id}"

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)

        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json

        # To ensure that sending message in socket can only be made by the app itself.
        key = message.pop("key")
        if key and key == settings.SOCKET_SECRET:
            await self.channel_layer.group_send(
                self.room_group_name, {"type": "chat_message", "message": message}
            )

    async def chat_message(self, event):
        message = event["message"]
        # Add a validation to only allow socket messages to be sent from inside
        await self.send(text_data=json.dumps(message))


# class NotificationConsumer(AsyncWebsocketConsumer):
#     async def connect(self):
#         user_id = self.scope["url_route"]["kwargs"]["user_id"]
#         self.room_name = f"notification_{user_id}"
#         self.room_group_name = f"notification_{user_id}"

#         await self.channel_layer.group_add(self.room_group_name, self.channel_name)
#         await self.accept()

#     async def disconnect(self, close_code):
#         await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

#     async def receive(self, text_data):
#         text_data_json = json.loads(text_data)
#         notification = text_data_json
#         print(notification)

#         await self.channel_layer.group_send(
#             self.room_group_name,
#             {"type": "notification_message", "notification": notification},
#         )

#     async def notification_message(self, event):
#         notification = event["notification"]
#         await self.send(text_data=json.dumps(notification))
