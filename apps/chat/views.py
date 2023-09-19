from django.db.models import Q, Prefetch
from adrf.views import APIView
from drf_spectacular.utils import extend_schema, OpenApiParameter
from asgiref.sync import sync_to_async
from apps.chat.models import Chat, Message
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
    MessagesSerializer,
)

tags = ["Chats"]


class ChatsView(APIView):
    serializer_class = ChatSerializer
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
