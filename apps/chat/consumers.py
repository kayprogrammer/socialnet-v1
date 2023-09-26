from channels.generic.websocket import AsyncWebsocketConsumer
import json

from django.conf import settings
from django.db.models import Q
from apps.chat.models import Chat
from apps.accounts.models import User


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        err = self.scope["error"]
        id = self.scope["url_route"]["kwargs"][
            "id"
        ]  # ID is either the chat id or recipient id if its the first message of a dm
        self.room_name = f"chat_{id}"
        self.room_group_name = f"chat_{id}"
        await self.accept()

        if not err.get("message"):  # Check for auth errors
            # Validate
            chat, obj_user = await self.get_object(id)
            print(chat, obj_user)
            if not chat and not obj_user:
                await self.send_error_message(
                    {"type": "invalid_input", "message": "Invalid ID"}
                )
                await self.close(code=1001)
            else:
                await self.channel_layer.group_add(
                    self.room_group_name, self.channel_name
                )

        else:
            await self.send_error_message(err)
            await self.close(code=4001)

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json

        # To ensure that sending message in socket can only be made by the app itself. (move to notifications endpoint later)
        key = message.pop("key")
        if key and key == settings.SOCKET_SECRET:
            await self.channel_layer.group_send(
                self.room_group_name, {"type": "chat_message", "message": message}
            )

    async def get_object(self, id):
        user = self.scope["user"]
        chat, obj_user = None, None
        if user.id != id:
            chat = await Chat.objects.filter(
                Q(owner=user) | Q(users__id=user.id)
            ).aget_or_none(id=id)
            if not chat:
                obj_user = await User.objects.aget_or_none(id=id)
        else:
            obj_user = user

        self.scope["chat"] = chat
        self.scope["obj_user"] = obj_user
        return chat, obj_user

    async def chat_message(self, event):
        message = event["message"]
        # Add a validation to only allow socket messages to be sent from inside
        await self.send(text_data=json.dumps(message))

    async def send_error_message(self, error):
        err = {"status": "error"} | error
        # Send an error message to the client
        await self.send(json.dumps(err))
