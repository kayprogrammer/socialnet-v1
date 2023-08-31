from adrf.views import APIView
from apps.accounts.auth import Authentication

from apps.common.error import ErrorCode
from apps.common.utils import IsAuthenticatedCustom

from .emails import Util

from .models import Jwt, Otp, User
from .serializers import (
    LoginResponseSerializer,
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
from apps.common.serializers import (
    ErrorResponseSerializer,
    ErrorDataResponseSerializer,
    SuccessResponseSerializer,
)

from apps.common.exceptions import RequestError

tags = ["Auth"]


class RegisterView(APIView):
    serializer_class = RegisterSerializer

    @extend_schema(
        summary="Register a new user",
        description="This endpoint registers new users into our application",
        tags=tags,
        responses={201: RegisterResponseSerializer, 422: ErrorDataResponseSerializer},
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


class VerifyEmailView(APIView):
    serializer_class = VerifyOtpSerializer

    @extend_schema(
        summary="Verify a user's email",
        description="This endpoint verifies a user's email",
        responses={
            200: SuccessResponseSerializer,
            422: ErrorDataResponseSerializer,
            404: ErrorResponseSerializer,
            498: ErrorResponseSerializer,
        },
        tags=tags,
    )
    async def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]
        otp_code = serializer.validated_data["otp"]

        user = await User.objects.aget_or_none(email=email)

        if not user:
            raise RequestError(
                err_code=ErrorCode.INCORRECT_EMAIL,
                err_msg="Incorrect Email",
                status_code=404,
            )

        if user.is_email_verified:
            return CustomResponse.success(message="Email already verified")

        otp = await Otp.objects.aget_or_none(user=user)
        if not otp or otp.code != otp_code:
            raise RequestError(
                err_code=ErrorCode.INCORRECT_OTP,
                err_msg="Incorrect Otp",
                status_code=404,
            )
        if otp.check_expiration():
            raise RequestError(
                err_code=ErrorCode.EXPIRED_OTP, err_msg="Expired Otp", status_code=498
            )

        user.is_email_verified = True
        await user.asave()
        await otp.adelete()

        # Send welcome email
        Util.welcome_email(user)
        return CustomResponse.success(
            message="Account verification successful", status_code=200
        )


class ResendVerificationEmailView(APIView):
    serializer_class = ResendOtpSerializer

    @extend_schema(
        summary="Resend Verification Email",
        description="This endpoint resends new otp to the user's email",
        responses={
            200: SuccessResponseSerializer,
            422: ErrorDataResponseSerializer,
            404: ErrorResponseSerializer,
        },
        tags=tags,
    )
    async def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]
        user = await User.objects.aget_or_none(email=email)
        if not user:
            raise RequestError(
                err_code=ErrorCode.INCORRECT_EMAIL,
                err_msg="Incorrect Email",
                status_code=404,
            )
        if user.is_email_verified:
            return CustomResponse.success(message="Email already verified")

        # Send verification email
        await Util.send_activation_otp(user)
        return CustomResponse.success(
            message="Verification email sent", status_code=200
        )


class SendPasswordResetOtpView(APIView):
    serializer_class = ResendOtpSerializer

    @extend_schema(
        summary="Send Password Reset Otp",
        description="This endpoint sends new password reset otp to the user's email",
        responses={
            200: SuccessResponseSerializer,
            422: ErrorDataResponseSerializer,
            404: ErrorResponseSerializer,
        },
        tags=tags,
    )
    async def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]

        user = await User.objects.aget_or_none(email=email)
        if not user:
            raise RequestError(
                err_code=ErrorCode.INCORRECT_EMAIL,
                err_msg="Incorrect Email",
                status_code=404,
            )

        # Send password reset email
        await Util.send_password_change_otp(user)
        return CustomResponse.success(message="Password otp sent")


class SetNewPasswordView(APIView):
    serializer_class = SetNewPasswordSerializer

    @extend_schema(
        summary="Set New Password",
        description="This endpoint verifies the password reset otp",
        responses={
            200: SuccessResponseSerializer,
            422: ErrorDataResponseSerializer,
            404: ErrorResponseSerializer,
            498: ErrorResponseSerializer,
        },
        tags=tags,
    )
    async def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        email = data["email"]
        code = data["otp"]
        password = data["password"]

        user = await User.objects.aget_or_none(email=email)
        if not user:
            raise RequestError(
                err_code=ErrorCode.INCORRECT_EMAIL,
                err_msg="Incorrect Email",
                status_code=404,
            )

        otp = await Otp.objects.aget_or_none(user=user)
        if not otp or otp.code != code:
            raise RequestError(
                err_code=ErrorCode.INCORRECT_OTP,
                err_msg="Incorrect Otp",
                status_code=404,
            )

        if otp.check_expiration():
            raise RequestError(
                err_code=ErrorCode.EXPIRED_OTP, err_msg="Expired Otp", status_code=498
            )

        user.set_password(password)
        await user.asave()

        # Send password reset success email
        Util.password_reset_confirmation(user)
        return CustomResponse.success(message="Password reset successful")


class LoginView(APIView):
    serializer_class = LoginSerializer

    @extend_schema(
        summary="Login a user",
        description="This endpoint generates new access and refresh tokens for authentication",
        responses={
            201: LoginResponseSerializer,
            422: ErrorDataResponseSerializer,
            401: ErrorResponseSerializer,
        },
        tags=tags,
    )
    async def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        email = data["email"]
        password = data["password"]

        user = await User.objects.aget_or_none(email=email)
        if not user or not user.check_password(password):
            raise RequestError(
                err_code=ErrorCode.INVALID_CREDENTIALS,
                err_msg="Invalid credentials",
                status_code=401,
            )

        if not user.is_email_verified:
            raise RequestError(
                err_code=ErrorCode.UNVERIFIED_USER,
                err_msg="Verify your email first",
                status_code=401,
            )
        await Jwt.objects.filter(user_id=user.id).adelete()

        # Create tokens and store in jwt model
        access = Authentication.create_access_token(
            {"user_id": str(user.id), "username": user.username}
        )
        refresh = Authentication.create_refresh_token()
        await Jwt.objects.acreate(user_id=user.id, access=access, refresh=refresh)
        return CustomResponse.success(
            message="Login successful",
            data={"access": access, "refresh": refresh},
            status_code=201,
        )


class RefreshTokensView(APIView):
    serializer_class = RefreshSerializer

    @extend_schema(
        summary="Refresh tokens",
        description="This endpoint refresh tokens by generating new access and refresh tokens for a user",
        responses={
            201: LoginResponseSerializer,
            422: ErrorDataResponseSerializer,
            401: ErrorResponseSerializer,
            404: ErrorResponseSerializer,
        },
        tags=tags,
    )
    async def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        token = data["refresh"]
        jwt = await Jwt.objects.select_related("user").aget_or_none(refresh=token)

        if not jwt:
            raise RequestError(
                err_code=ErrorCode.INVALID_TOKEN,
                err_msg="Refresh token does not exist",
                status_code=404,
            )
        if not Authentication.decode_jwt(token):
            raise RequestError(
                err_code=ErrorCode.INVALID_TOKEN,
                err_msg="Refresh token is invalid or expired",
                status_code=401,
            )

        access = Authentication.create_access_token(
            {"user_id": str(jwt.user_id), "username": jwt.user.username}
        )
        refresh = Authentication.create_refresh_token()

        jwt.access = access
        jwt.refresh = refresh
        await jwt.asave()

        return CustomResponse.success(
            message="Tokens refresh successful",
            data={"access": access, "refresh": refresh},
            status_code=201,
        )


class LogoutView(APIView):
    serializer_class = None
    permission_classes = (IsAuthenticatedCustom,)

    @extend_schema(
        summary="Logout a user",
        description="This endpoint logs a user out from our application",
        responses={
            200: SuccessResponseSerializer,
            401: ErrorResponseSerializer,
        },
        tags=tags,
    )
    async def get(self, request):
        await Jwt.objects.filter(user_id=request.user.id).adelete()
        return CustomResponse.success(message="Logout successful")
