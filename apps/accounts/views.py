from adrf.views import APIView

from apps.common.error import ErrorCode

from .emails import Util

from .models import Jwt, Otp, User
from .serializers import (
    LoginSerializer,
    RefreshSerializer,
    RegisterSerializer,
    RegisterResponseSerializer,
    ResendOtpSerializer,
    SetNewPasswordSerializer,
    VerifyOtpSerializer,
)
from drf_spectacular.utils import extend_schema
from apps.common.responses import CustomResponse

from apps.common.exceptions import RequestError
from asgiref.sync import sync_to_async


class RegisterView(APIView):
    serializer_class = RegisterSerializer

    @extend_schema(
        summary="Register a new user",
        description="This endpoint registers new users into our application",
        tags=["Auth"],
        responses={201: RegisterResponseSerializer},
    )
    async def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        # Check for existing user
        existing_user = await User.objects.aget_or_none(email=data["email"])
        if existing_user:
            raise RequestError(
                err_code=ErrorCode.INVALID_ENTRY,
                err_msg="Invalid Entry",
                status_code=422,
                data={"email": "Email already registered!"},
            )

        # Create user
        user = await User.objects.acreate_user(**data)

        # Send verification email
        await Util.send_activation_otp(user)

        return CustomResponse.success(
            message="Registration successful",
            data={"email": data["email"]},
            status_code=201,
        )
