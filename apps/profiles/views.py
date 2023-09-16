from django.db.models import F, Q, Case, When, Value, BooleanField
from adrf.views import APIView
from drf_spectacular.utils import extend_schema, OpenApiParameter
from asgiref.sync import sync_to_async
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


class ProfilesView(APIView):
    serializer_class = ProfileSerializer
    paginator_class = CustomPagination()
    paginator_class.page_size = 15
    permission_classes = (IsAuthenticatedOrGuestCustom,)

    async def get_queryset(self, current_user):
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


class CitiesView(APIView):
    serializer_class = CitySerializer

    @extend_schema(
        summary="Retrieve cities based on query params",
        description="This endpoint retrieves a first 10 cities that matches the query params",
        tags=tags,
        responses=CitiesResponseSerializer,
        parameters=[
            OpenApiParameter(
                name="name",
                description="""
                    Enter the name of the city
                """,
                required=False,
                type=str,
                location="query",
            ),
        ],
    )
    async def get(self, request):
        search_term = request.GET.get("name")
        cities = []
        message = "Cities Fetched"
        if search_term:
            search_term = re.sub(r"[^\w\s]", "", search_term)  # Remove special chars
            cities = await sync_to_async(list)(
                City.objects.filter(name__startswith=search_term).select_related(
                    "region", "country"
                )[:10]
            )
            cities = self.serializer_class(cities, many=True).data
        if len(cities) == 0:
            message = "No match found"
        return CustomResponse.success(message=message, data=cities)


class ProfileView(APIView):
    serializer_class = ProfileSerializer

    common_param = [
        OpenApiParameter(
            name="username",
            description="""
                Enter the username of the user
            """,
            required=True,
            type=str,
            location="path",
        ),
    ]

    async def get_object(self, username):
        user = await User.objects.select_related("city", "avatar").aget_or_none(
            username=username
        )
        if not user:
            raise RequestError(
                err_code=ErrorCode.NON_EXISTENT,
                err_msg="No user with that username",
                status_code=404,
            )
        return user

    @extend_schema(
        summary="Retrieve user's profile",
        description="This endpoint retrieves a particular user profile",
        tags=tags,
        responses=ProfileResponseSerializer,
        parameters=common_param,
    )
    async def get(self, request, *args, **kwargs):
        user = await self.get_object(kwargs.get("username"))
        serializer = self.serializer_class(user)
        return CustomResponse.success(
            message="User details fetched", data=serializer.data
        )


class ProfileUpdateDeleteView(APIView):
    permission_classes = (IsAuthenticatedCustom,)
    serializer_class = ProfileSerializer
    post_resp_serializer_class = ProfileCreateResponseDataSerializer

    @extend_schema(
        summary="Update user's profile",
        description=f"""
            This endpoint updates a particular user profile
            ALLOWED FILE TYPES: {", ".join(ALLOWED_IMAGE_TYPES)}
        """,
        tags=tags,
        responses=ProfileCreateResponseSerializer,
    )
    async def patch(self, request):
        user = request.user
        serializer = self.serializer_class(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        # Validate City ID Entry
        city_id = data.pop("city_id", None)
        if city_id:
            city = await City.objects.filter(id=city_id).afirst()
            if not city:
                raise RequestError(
                    err_code=ErrorCode.INVALID_ENTRY,
                    err_msg="Invalid Entry",
                    data={"city_id": "No city with that ID"},
                    status_code=422,
                )
            data["city"] = city

        # Handle file upload
        image_upload_status = False
        file_type = data.get("file_type")
        if file_type:
            image_upload_status = True
            avatar = user.avatar
            if avatar:
                avatar.resource_type = file_type
                await avatar.asave()
            else:
                avatar = await File.objects.acreate(resource_type=file_type)
            data.pop("file_type")
            data["avatar"] = avatar

        # Set attributes from data to user object
        user = set_dict_attr(user, data)
        await user.asave()
        serializer = self.post_resp_serializer_class(
            user, context={"image_upload_status": image_upload_status}
        )
        return CustomResponse.success(message="User updated", data=serializer.data)

    @extend_schema(
        summary="Delete user's account",
        description="This endpoint deletes a particular user's account",
        tags=tags,
        request=DeleteUserSerializer,
        responses={200: SuccessResponseSerializer},
    )
    async def post(self, request):
        user = request.user
        serializer = DeleteUserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        password = serializer.validated_data["password"]

        # Check if password is valid
        if not user.check_password(password):
            raise RequestError(
                err_code=ErrorCode.INVALID_CREDENTIALS,
                err_msg="Invalid Entry",
                status_code=422,
                data={"password": "Incorrect password"},
            )

        # Delete user
        await user.adelete()
        return CustomResponse.success(message="User deleted")


class FriendsView(APIView):
    serializer_class = ProfileSerializer
    paginator_class = CustomPagination()
    paginator_class.page_size = 20
    permission_classes = (IsAuthenticatedCustom,)

    async def get_queryset(self, user):
        friends = (
            Friend.objects.filter(Q(requester=user) | Q(requestee=user))
            .filter(status="ACCEPTED")
            .select_related("requester", "requestee")
        )
        friend_ids = friends.annotate(
            friend_id=Case(
                When(requester=user, then=F("requestee")),
                When(requestee=user, then=F("requester")),
            )
        ).values_list("friend_id", flat=True)
        users = User.objects.filter(id__in=friend_ids).select_related("avatar", "city")
        return await sync_to_async(list)(users)

    @extend_schema(
        summary="Retrieve Friends",
        description="This endpoint retrieves friends of a user",
        tags=tags,
        responses=ProfilesResponseSerializer,
        parameters=[
            OpenApiParameter(
                name="page",
                description="Retrieve a particular page of friends. Defaults to 1",
                required=False,
                type=int,
            )
        ],
    )
    async def get(self, request):
        user = request.user
        friends = await self.get_queryset(user)
        paginated_friends = self.paginator_class.paginate_queryset(friends, request)
        serializer = self.serializer_class(paginated_friends, many=True)
        return CustomResponse.success(message="Friends fetched", data=serializer.data)

    async def get_other_user_and_friend(self, user, username, status=None):
        # Get and validate username existence
        other_user = await User.objects.aget_or_none(username=username)
        if not other_user:
            raise RequestError(
                err_code=ErrorCode.NON_EXISTENT,
                err_msg="User does not exist!",
                status_code=404,
            )

        friend = Friend.objects.filter(
            Q(requester=user, requestee=other_user)
            | Q(requester=other_user, requestee=user)
        )
        if status:
            friend = friend.filter(status=status)
        friend = await friend.aget_or_none()
        return other_user, friend

    @extend_schema(
        summary="Send Or Delete Friend Request",
        description="This endpoint sends or delete friend requests",
        tags=tags,
        request=SendFriendRequestSerializer,
        responses=SuccessResponseSerializer,
    )
    async def post(self, request):
        user = request.user
        serializer = SendFriendRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        other_user, friend = await self.get_other_user_and_friend(
            user, serializer.validated_data["username"]
        )
        message = "Friend Request sent"
        status_code = 201
        if friend:
            status_code = 200
            message = "Friend Request removed"
            if user.id != friend.requester_id:
                raise RequestError(
                    err_code=ErrorCode.NOT_ALLOWED,
                    err_msg="The user already sent you a friend request!",
                    status_code=403,
                )

            await friend.adelete()
        else:
            await Friend.objects.acreate(requester=user, requestee=other_user)

        return CustomResponse.success(message=message, status_code=status_code)

    @extend_schema(
        summary="Accept Or Reject a Friend Request",
        description="""
            This endpoint accepts or reject a friend request
            status choices:
            - true - accepted
            - false - rejected
        """,
        tags=tags,
        request=AcceptFriendRequestSerializer,
        responses=SuccessResponseSerializer,
    )
    async def put(self, request):
        user = request.user
        serializer = AcceptFriendRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        _, friend = await self.get_other_user_and_friend(
            user, serializer.validated_data["username"], "PENDING"
        )
        if not friend:
            raise RequestError(
                err_code=ErrorCode.NON_EXISTENT,
                err_msg="No pending friend request exist between you and that user",
                status_code=401,
            )
        if friend.requester_id == user.id:
            raise RequestError(
                err_code=ErrorCode.NOT_ALLOWED,
                err_msg="You cannot accept or reject a friend request you sent ",
                status_code=403,
            )

        # Update or delete friend request based on status
        status = serializer.validated_data["status"]
        if status:
            msg = "Accepted"
            friend.status = "ACCEPTED"
            await friend.asave()
        else:
            msg = "Rejected"
            await friend.adelete()

        return CustomResponse.success(message=f"Friend Request {msg}", status_code=200)
