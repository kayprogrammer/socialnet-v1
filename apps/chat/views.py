from django.db.models import F, Q, Prefetch
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
    ChatSerializer,
    ChatsResponseSerializer,
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
                    to_attr="latest_messages",
                )
            )
            .distinct()
        )
        chats = await sync_to_async(list)(chats)
        return chats

    @extend_schema(
        summary="Retrieve User Chats",
        description="This endpoint retrieves a paginated list of the current user chats",
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
