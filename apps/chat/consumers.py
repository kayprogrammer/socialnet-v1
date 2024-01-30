from django.conf import settings
from apps.chat.models import Chat, Message
from apps.accounts.models import User
from apps.chat.serializers import MessageSerializer
from apps.chat.socket_serializers import SocketMessageSerializer
from apps.common.consumers import BaseConsumer
from apps.common.error import ErrorCode
from uuid import UUID
import json
import websockets


class ChatConsumer(BaseConsumer):
    async def connect(self):
        err = self.scope["error"]
        id = self.scope["url_route"]["kwargs"][
            "id"
        ]  # ID is either the chat id or recipient id if its the first message of a dm
        self.room_name = f"chat_{id}"
        self.room_group_name = f"chat_{id}"
        await self.accept()

        if err.get("message"):  # Check for auth errors
            await self.send_error_message(err)
            return await self.close(code=4001)

        # Validate chat membership
        await self.validate_chat_membership(id)

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        user = self.scope["user"]
        user_id = user.id if isinstance(user, User) else None

        # Validate entry
        data, validated = await self.validate_entry(text_data, SocketMessageSerializer)
        if not validated:
            return await self.send_error_message(data)
        status = data["status"]
        if status == "DELETED" and user != settings.SOCKET_SECRET:
            return await self.send_error_message(
                {
                    "type": ErrorCode.INVALID_ENTRY,
                    "code": 4001,
                    "message": "Not allowed to send deletion socket",
                },
            )
        message_data = data
        if status != "DELETED":
            message = await Message.objects.select_related(
                "sender", "sender__avatar", "file"
            ).aget_or_none(id=data["id"])
            if not message:
                return await self.send_error_message(
                    {
                        "type": ErrorCode.NON_EXISTENT,
                        "message": "Invalid message ID",
                    }
                )
            if message.sender_id != user_id:
                return await self.send_error_message(
                    {
                        "type": ErrorCode.INVALID_OWNER,
                        "message": "Message isn't yours",
                    }
                )
            data = MessageSerializer(message).data
            data.pop("id")
            message_data = message_data | data

        await self.channel_layer.group_send(
            self.room_group_name, {"type": "chat_message", "message": message_data}
        )

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
        if user != settings.SOCKET_SECRET:
            chat, obj_user = await self.get_objects(id)
            if not chat and not obj_user:  # If no chat nor user
                await self.send_error_message(
                    {"type": "invalid_input", "message": "Invalid ID"}
                )
                return await self.close(code=1001)
            if (
                chat and user not in chat.users.all() and user.id != chat.owner_id
            ):  # If chat but user is not a member
                await self.send_error_message(
                    {
                        "type": "invalid_member",
                        "message": "You're not a member of this chat",
                    }
                )
                return await self.close(code=1001)
        # Add group and channel name to channel layer
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)

    async def chat_message(self, event):
        message = event["message"]
        obj_user = self.scope.get("obj_user")
        user = self.scope["user"]

        if obj_user:
            # Ensure that reading messages from a user id can only be done by the owner
            if user == obj_user:
                await self.send(text_data=json.dumps(message))
        else:
            await self.send(text_data=json.dumps(message))


async def send_message_deletion_in_socket(secured: bool, host: str, chat_id: UUID, message_id: UUID):
    websocket_scheme = "wss://" if secured else "ws://"
    uri = f"{websocket_scheme}{host}/api/v1/ws/chats/{chat_id}/"
    chat_data = {
        "id": str(message_id),
        "status": "DELETED",
    }
    headers = [
        ("Authorization", settings.SOCKET_SECRET),
    ]
    async with websockets.connect(uri, extra_headers=headers) as websocket:
        # Send a notification to the WebSocket server
        await websocket.send(json.dumps(chat_data))
        await websocket.close()
