from django.db.models import Count
from adrf.views import APIView
from rest_framework.pagination import PageNumberPagination
from drf_spectacular.utils import extend_schema, OpenApiParameter
from asgiref.sync import sync_to_async
from apps.common.exceptions import RequestError
from apps.common.error import ErrorCode
from apps.common.serializers import ErrorResponseSerializer, SuccessResponseSerializer
from apps.common.responses import CustomResponse

from apps.common.file_types import ALLOWED_IMAGE_TYPES
from apps.accounts.models import User
from apps.common.utils import set_dict_attr
from .serializers import ProfileResponseSerializer, ProfileSerializer
from cities_light.models import Country, Region, City

tags = ["Profiles"]


class CountriesView(APIView):
    async def get(self, request):
        countries = await sync_to_async(list)(
            Country.objects.values("name", "slug", "code")
        )


class StatesView(APIView):
    async def get(self, request):
        states = await sync_to_async(list)(Region.objects.all())


class CitiesView(APIView):
    async def get(self, request):
        regions = await sync_to_async(list)(City.objects.all())


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
        user = await User.objects.select_related(
            "country", "state", "city"
        ).aget_or_none(username=username)
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

    @extend_schema(
        summary="Update user's profile",
        description="This endpoint updates a particular user profile",
        tags=tags,
        responses=ProfileResponseSerializer,
        parameters=common_param,
    )
    async def patch(self, request, *args, **kwargs):
        user = await self.get_object(kwargs.get("username"))
        serializer = self.serializer_class(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        user = set_dict_attr(user, data)
        serializer = self.serializer_class(user)
        return CustomResponse.success(message="User updated", data=serializer.data)
