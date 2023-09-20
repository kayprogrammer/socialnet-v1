from django.db.models import Q, Prefetch
from adrf.views import APIView
from drf_spectacular.utils import extend_schema, OpenApiParameter
from asgiref.sync import sync_to_async
from apps.chat.models import Chat, Message
from apps.chat.utils import create_file
from apps.common.exceptions import RequestError
from apps.common.error import ErrorCode
from apps.common.models import File
from apps.common.serializers import SuccessResponseSerializer
from apps.common.responses import CustomResponse

from apps.common.file_types import ALLOWED_IMAGE_TYPES
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
    MessageCreateResponseDataSerializer,
    MessageCreateResponseSerializer,
    MessageSerializer,
    MessagesSerializer,
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
        summary="Send a  message",
        description="""
            This endpoint sends a message.
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
                err_msg="User has not chat with that ID",
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
        chat = await self.get_object(user, kwargs.get("chat_id"))
        messages = await sync_to_async(list)(chat.lmessages)
        serializer = self.serializer_class({"chat": chat, "messages": messages})
        return CustomResponse.success(message="Messages fetched", data=serializer.data)
