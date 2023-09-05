from django.db.models import Count, F, Q
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
from .serializers import (
    CitiesResponseSerializer,
    CitySerializer,
    ProfileResponseSerializer,
    ProfileSerializer,
)
from cities_light.models import Country, Region, City
import re

tags = ["Profiles"]


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
        user = await User.objects.select_related("city").aget_or_none(username=username)
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
