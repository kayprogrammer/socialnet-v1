from django.db.models import F, Q, Case, When, Value, BooleanField
from adrf.views import APIView
from drf_spectacular.utils import extend_schema, OpenApiParameter
from asgiref.sync import sync_to_async
from apps.chat.models import Chat
from apps.common.exceptions import RequestError
from apps.common.error import ErrorCode
from apps.common.models import File
from apps.common.serializers import SuccessResponseSerializer
from apps.common.responses import CustomResponse

from apps.common.file_types import ALLOWED_IMAGE_TYPES
from apps.accounts.models import User
from apps.common.utils import (
    IsAuthenticatedCustom,
    IsAuthenticatedOrGuestCustom,
    set_dict_attr,
)
from apps.common.paginators import CustomPagination
from apps.profiles.models import Friend
from .serializers import (
    AcceptFriendRequestSerializer,
    ChatSerializer,
    CitiesResponseSerializer,
    CitySerializer,
    ProfileCreateResponseDataSerializer,
    ProfileCreateResponseSerializer,
    ProfileResponseSerializer,
    ProfileSerializer,
    DeleteUserSerializer,
    ProfilesResponseSerializer,
    SendFriendRequestSerializer,
)
from cities_light.models import City
import re

tags = ["Profiles"]


class ChatsView(APIView):
    serializer_class = ChatSerializer
    paginator_class = CustomPagination()
    paginator_class.page_size = 15
    permission_classes = (IsAuthenticatedCustom,)

    async def get_queryset(self, current_user):
        chats = Chat.objects.filter(Q(owner=current_user) | Q(users__id=current_user.id)).select_related("owner", "image")
        users = User.objects.select_related("avatar", "city")
        if current_user:
            users = users.exclude(id=current_user.id)
            if current_user.city:
                # Order by the current user region or country
                city = current_user.city
                region = city.region.name if city.region else None
                country = city.country.name
                order_by_val = (
                    Q(city__region__name=region)
                    if region
                    else Q(city__country__name=country)
                )

                users = users.annotate(
                    ordering_field=Case(
                        When(order_by_val, then=Value(True)),
                        default=Value(
                            False
                        ),  # Use False as a default value if the condition doesn't match
                        output_field=BooleanField(),
                    )
                ).annotate(
                    has_city=Case(
                        When(city__isnull=False, then=Value(True)),
                        default=Value(False),
                        output_field=BooleanField(),
                    )
                )
                # Order the users by the 'ordering_field' and "has_city" field in descending order
                users = users.order_by("-has_city", "-ordering_field")

        users = await sync_to_async(list)(users)
        return users

    @extend_schema(
        summary="Retrieve Users",
        description="This endpoint retrieves a paginated list of users",
        tags=tags,
        responses=ProfilesResponseSerializer,
        parameters=[
            OpenApiParameter(
                name="page",
                description="Retrieve a particular page of users. Defaults to 1",
                required=False,
                type=int,
            )
        ],
    )
    async def get(self, request, *args, **kwargs):
        user = request.user
        users = await self.get_queryset(user)
        paginated_users = self.paginator_class.paginate_queryset(users, request)
        serializer = self.serializer_class(paginated_users, many=True)
        return CustomResponse.success(message="Users fetched", data=serializer.data)
