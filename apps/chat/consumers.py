import json

from apps.chat.models import Chat
from apps.accounts.models import User
from apps.common.consumers import BaseConsumer


class ChatConsumer(BaseConsumer):
    async def connect(self):
        err = self.scope["error"]
        id = self.scope["url_route"]["kwargs"][
            "id"
        ]  # ID is either the chat id or recipient id if its the first message of a dm
        self.room_name = f"chat_{id}"
        self.room_group_name = f"chat_{id}"
        await self.accept()

        if not err.get("message"):  # Check for auth errors
            # Validate chat membership
            await self.validate_chat_membership(id)
        else:
            await self.send_error_message(err)
            await self.close(code=4001)

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        # Validate entry
        data, validated = await self.validate_entry(text_data)
        if validated:
            await self.channel_layer.group_send(
                self.room_group_name, {"type": "chat_message", "message": data}
            )
        else:
            await self.send_error_message(data)

    async def get_objects(self, id):
        # Retrieve a chat or user based on ID in the path
        user = self.scope["user"]
        chat, obj_user = None, None
        if user.id != id:
            chat = await Chat.objects.prefetch_related("users").aget_or_none(id=id)
            if not chat:
                obj_user = await User.objects.aget_or_none(id=id)
        else:
            obj_user = user

        self.scope["chat"] = chat
        self.scope["obj_user"] = obj_user
        return chat, obj_user

    async def validate_chat_membership(self, id):
        user = self.scope["user"]
        chat, obj_user = await self.get_objects(id)

        if not chat and not obj_user:  # If no chat nor user
            await self.send_error_message(
                {"type": "invalid_input", "message": "Invalid ID"}
            )
            await self.close(code=1001)
        elif (
            chat and user not in chat.users.all() and user.id != chat.owner_id
        ):  # If chat but user is not a member
            await self.send_error_message(
                {
                    "type": "invalid_member",
                    "message": "You're not a member of this chat",
                }
            )
            await self.close(code=1001)
        else:  # Add group and channel name to channel layer
            await self.channel_layer.group_add(self.room_group_name, self.channel_name)

    async def chat_message(self, event):
        message = event["message"]
        obj_user = self.scope["obj_user"]
        user = self.scope["user"]

        if (
            user == obj_user
        ):  # Ensure that reading messages from a user id can only be done by the owner
            await self.send(text_data=json.dumps(message))
