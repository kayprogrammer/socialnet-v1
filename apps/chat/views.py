import asyncio
from django.db.models import Q, Prefetch
from adrf.views import APIView
from drf_spectacular.utils import extend_schema, OpenApiParameter
from asgiref.sync import sync_to_async
from apps.chat.models import Chat, Message
from apps.chat.utils import create_file, update_group_chat_users
from apps.common.exceptions import RequestError
from apps.common.error import ErrorCode
from apps.common.serializers import SuccessResponseSerializer
from apps.common.responses import CustomResponse

from apps.common.file_types import ALLOWED_FILE_TYPES
from apps.accounts.models import User
from apps.common.utils import (
    IsAuthenticatedCustom,
    set_dict_attr,
)
from apps.common.paginators import CustomPagination
from .serializers import (
    ChatResponseSerializer,
    ChatSerializer,
    ChatsResponseSerializer,
    GroupChatCreateResponseDataSerializer,
    GroupChatCreateResponseSerializer,
    GroupChatSerializer,
    MessageCreateResponseDataSerializer,
    MessageCreateResponseSerializer,
    MessageSerializer,
    MessagesSerializer,
    UpdateMessageSerializer,
)

tags = ["Chats"]


class ChatsView(APIView):
    serializer_class = ChatSerializer
    post_serializer_class = MessageSerializer
    paginator_class = CustomPagination()
    paginator_class.page_size = 200
    permission_classes = (IsAuthenticatedCustom,)

    async def get_queryset(self, user):
        chats = (
            Chat.objects.filter(Q(owner=user) | Q(users__id=user.id))
            .select_related("owner", "owner__avatar", "image")
            .prefetch_related(
                Prefetch(
                    "messages",
                    queryset=Message.objects.select_related(
                        "sender", "sender__avatar", "file"
                    ).order_by("-created_at"),
                    to_attr="lmessages",
                )
            )
            .distinct()
        )
        chats = await sync_to_async(list)(chats)
        return chats

    @extend_schema(
        summary="Retrieve User Chats",
        description="""
            This endpoint retrieves a paginated list of the current user chats
            Only chat with type "GROUP" have name, image and description.
        """,
        tags=tags,
        responses=ChatsResponseSerializer,
        parameters=[
            OpenApiParameter(
                name="page",
                description="Retrieve a particular page of chats. Defaults to 1",
                required=False,
                type=int,
            )
        ],
    )
    async def get(self, request, *args, **kwargs):
        user = request.user
        chats = await self.get_queryset(user)
        paginated_chats = self.paginator_class.paginate_queryset(chats, request)
        serializer = self.serializer_class(paginated_chats, many=True)
        return CustomResponse.success(message="Chats fetched", data=serializer.data)

    @extend_schema(
        summary="Send a message",
        description=f"""
            This endpoint sends a message.
            You must either send a text or a file or both.
            If there's no chat_id, then its a new chat and you must set username and leave chat_id
            If chat_id is available, then ignore username and set the correct chat_id
            The file_upload_data in the response is what is used for uploading the file to cloudinary from client
            ALLOWED FILE TYPES: {", ".join(ALLOWED_FILE_TYPES)}
        """,
        tags=tags,
        responses={201: MessageCreateResponseSerializer},
    )
    async def post(self, request, *args, **kwargs):
        user = request.user
        serializer = self.post_serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        chat_id = data.get("chat_id")
        username = data.get("username")

        # For sending
        chat = None
        if not chat_id:
            # Create a new chat dm with current user and recipient user
            recipient_user = await User.objects.aget_or_none(username=username)
            if not recipient_user:
                raise RequestError(
                    err_code=ErrorCode.INVALID_ENTRY,
                    err_msg="Invalid entry",
                    status_code=422,
                    data={"username": "No user with that username"},
                )

            chat = (
                await Chat.objects.filter(ctype="DM")
                .filter(
                    Q(owner=user, users__id=recipient_user.id)
                    | Q(owner=recipient_user, users__id=user.id)
                )
                .aget_or_none()
            )
            # Check if a chat already exists between both users
            if chat:
                raise RequestError(
                    err_code=ErrorCode.INVALID_ENTRY,
                    err_msg="Invalid entry",
                    status_code=422,
                    data={
                        "username": "A chat already exist between you and the recipient"
                    },
                )
            chat = await Chat.objects.acreate(owner=user, ctype="DM")
            await chat.users.aadd(recipient_user)
        else:
            # Get the chat with chat id and check if the current user is the owner or the recipient
            chat = await Chat.objects.filter(
                Q(owner=user) | Q(users__id=user.id)
            ).aget_or_none(id=chat_id)
            if not chat:
                raise RequestError(
                    err_code=ErrorCode.NON_EXISTENT,
                    err_msg="User has not chat with that ID",
                    status_code=404,
                )

        # Create Message
        file = await create_file(data.get("file_type"))
        file_upload_status = True if file else False
        message = await Message.objects.acreate(
            chat=chat, sender=user, text=data.get("text"), file=file
        )
        serializer = MessageCreateResponseDataSerializer(
            message, context={"file_upload_status": file_upload_status}
        )
        return CustomResponse.success(
            message="Message sent", data=serializer.data, status_code=201
        )


class ChatView(APIView):
    serializer_class = MessagesSerializer
    permission_classes = (IsAuthenticatedCustom,)

    async def get_object(self, user, chat_id):
        chat = (
            await Chat.objects.filter(Q(owner=user) | Q(users__id=user.id))
            .select_related("owner", "owner__avatar", "image")
            .prefetch_related(
                Prefetch(
                    "messages",
                    queryset=Message.objects.select_related(
                        "sender", "sender__avatar", "file"
                    ).order_by("-created_at"),
                    to_attr="lmessages",
                ),
                Prefetch(
                    "users",
                    queryset=User.objects.select_related("avatar"),
                    to_attr="recipients",
                ),
            )
            .aget_or_none(id=chat_id)
        )
        if not chat:
            raise RequestError(
                err_code=ErrorCode.NON_EXISTENT,
                err_msg="User has no chat with that ID",
                status_code=404,
            )
        return chat

    @extend_schema(
        summary="Retrieve messages from a Chat",
        description="""
            This endpoint retrieves all messages in a chat.
        """,
        tags=tags,
        responses=ChatResponseSerializer,
    )
    async def get(self, request, *args, **kwargs):
        user = request.user
        chat = await self.get_object(user, kwargs["chat_id"])
        messages = await sync_to_async(list)(chat.lmessages)
        serializer = self.serializer_class({"chat": chat, "messages": messages})
        return CustomResponse.success(message="Messages fetched", data=serializer.data)

    @extend_schema(
        summary="Update a Group Chat",
        description="""
            This endpoint updates a group chat.
        """,
        tags=tags,
        request=GroupChatSerializer,
        responses={200: GroupChatCreateResponseSerializer},
    )
    async def patch(self, request, *args, **kwargs):
        user = request.user
        chat = await Chat.objects.select_related("image").aget_or_none(
            owner=user, id=kwargs["chat_id"], ctype="GROUP"
        )
        if not chat:
            raise RequestError(
                err_code=ErrorCode.NON_EXISTENT,
                err_msg="User owns no group chat with that ID",
                status_code=404,
            )

        serializer = GroupChatSerializer(
            data=request.data, partial=True, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        # Handle File Upload
        file_type = data.pop("file_type", None)
        file_upload_status = False
        if file_type:
            file_upload_status = True
            if chat.image:
                chat.image.resource_type = file_type
                await chat.image.asave()
            else:
                file = await create_file(file_type)
                data["image"] = file

        # Handle Users Upload or Remove
        usernames_to_add = data.pop("usernames_to_add", None)
        usernames_to_remove = data.pop("usernames_to_remove", None)

        if usernames_to_add:
            users_to_add = await sync_to_async(list)(
                User.objects.filter(username__in=usernames_to_add).select_related(
                    "avatar"
                )
            )
            await sync_to_async(update_group_chat_users)(chat, "add", users_to_add)
        if usernames_to_remove:
            users_to_remove = await sync_to_async(list)(
                User.objects.filter(username__in=usernames_to_remove)
            )
            await sync_to_async(update_group_chat_users)(
                chat, "remove", users_to_remove
            )

        chat = set_dict_attr(chat, data)
        await chat.asave()
        chat.recipients = await sync_to_async(list)(chat.users.select_related("avatar"))

        serializer = GroupChatCreateResponseDataSerializer(
            chat, context={"file_upload_status": file_upload_status, "request": request}
        )
        return CustomResponse.success(message="Chat updated", data=serializer.data)

    @extend_schema(
        summary="Delete a Group Chat",
        description="""
            This endpoint deletes a group chat.
        """,
        tags=tags,
        responses={200: SuccessResponseSerializer},
    )
    async def delete(self, request, *args, **kwargs):
        user = request.user
        chat = await Chat.objects.aget_or_none(
            owner=user, id=kwargs["chat_id"], ctype="GROUP"
        )
        if not chat:
            raise RequestError(
                err_code=ErrorCode.NON_EXISTENT,
                err_msg="User owns no group chat with that ID",
                status_code=404,
            )
        await chat.adelete()
        return CustomResponse.success(message="Group Chat Deleted")


class MessageView(APIView):
    permission_classes = (IsAuthenticatedCustom,)
    serializer_class = UpdateMessageSerializer

    async def get_object(self, message_id, user):
        message = await Message.objects.select_related(
            "sender", "chat", "sender__avatar", "file"
        ).aget_or_none(id=message_id, sender=user)
        if not message:
            raise RequestError(
                err_code=ErrorCode.NON_EXISTENT,
                err_msg="User has no message with that ID",
                status_code=404,
            )
        return message

    @extend_schema(
        summary="Update a message",
        description=f"""
            This endpoint updates a message.
            You must either send a text or a file or both.
            The file_upload_data in the response is what is used for uploading the file to cloudinary from client
            ALLOWED FILE TYPES: {", ".join(ALLOWED_FILE_TYPES)}
        """,
        tags=tags,
        responses={200: MessageCreateResponseSerializer},
    )
    async def put(self, request, *args, **kwargs):
        user = request.user
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        message = await self.get_object(kwargs["message_id"], user)
        # Handle File Upload
        file_upload_status = False
        file_type = data.pop("file_type", None)
        if file_type:
            file_upload_status = True
            if message.file:
                message.file.resource_type = file_type
                await message.file.asave()
            else:
                file = await create_file(file_type)
                data["file"] = file

        message = set_dict_attr(message, data)
        await message.asave()

        serializer = MessageCreateResponseDataSerializer(
            message, context={"file_upload_status": file_upload_status}
        )
        return CustomResponse.success(message="Message updated", data=serializer.data)

    @extend_schema(
        summary="Delete a message",
        description="""
            This endpoint deletes a message.
        """,
        tags=tags,
        responses={200: SuccessResponseSerializer},
    )
    async def delete(self, request, *args, **kwargs):
        user = request.user
        message = await self.get_object(kwargs["message_id"], user)
        chat = message.chat
        messages_count = await chat.messages.acount()

        # Delete message and chat if its the last message in the dm being deleted
        if messages_count == 1 and chat.ctype == "DM":
            await chat.adelete()  # Message deletes if chat gets deleted (CASCADE)
        else:
            await message.adelete()
        return CustomResponse.success(message="Message deleted")


class ChatGroupCreateView(APIView):
    permission_classes = (IsAuthenticatedCustom,)
    serializer_class = GroupChatSerializer

    @extend_schema(
        summary="Create a group chat",
        description="""
            This endpoint creates a group chat.
            The users_entry field should be a list of usernames you want to add to the group.
            Note: You cannot add more than 99 users in a group (1 owner + 99 other users = 100 users total)
        """,
        tags=tags,
        responses={201: GroupChatCreateResponseSerializer},
    )
    async def post(self, request):
        user = request.user
        serializer = self.serializer_class(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        data.update({"owner": user, "ctype": "GROUP"})
        # Handle File Upload
        file_type = data.pop("file_type", None)
        file_upload_status = False
        if file_type:
            file_upload_status = True
            file = await create_file(file_type)
            data["image"] = file

        # Handle Users Upload or Remove
        usernames_to_add = data.pop("usernames_to_add")
        users_to_add = await sync_to_async(list)(
            User.objects.filter(username__in=usernames_to_add)
            .exclude(id=user.id)
            .select_related("avatar")
        )
        if len(users_to_add) < 1:
            raise RequestError(
                err_code=ErrorCode.INVALID_ENTRY,
                err_msg="Invalid Entry",
                data={"users_entry": "Enter at least one valid username"},
                status_code=422,
            )

        # Create Chat
        chat = await Chat.objects.acreate(**data)
        chat.recipients = users_to_add
        await sync_to_async(update_group_chat_users)(chat, "add", users_to_add)

        serializer = GroupChatCreateResponseDataSerializer(
            chat, context={"file_upload_status": file_upload_status, "request": request}
        )
        return CustomResponse.success(
            message="Chat created", data=serializer.data, status_code=201
        )
