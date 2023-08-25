from rest_framework.permissions import BasePermission
from apps.accounts.auth import Authentication
from apps.accounts.models import User, Jwt
from apps.common.exceptions import RequestError
from apps.common.error import ErrorCode

from uuid import UUID


class IsAuthenticatedCustom(BasePermission):
    def has_permission(self, request, view):
        http_auth = request.META.get("HTTP_AUTHORIZATION")
        if not http_auth:
            raise RequestError(err_code=ErrorCode.INVALID_AUTH, err_msg="Auth Bearer not provided!", status_code=401)
        user = Authentication.decodeAuthorization(http_auth)
        if not user:
            raise RequestError(
                err_code=ErrorCode.INVALID_TOKEN, 
                err_msg="Auth Token is Invalid or Expired!", status_code=401
            )
        request.user = user
        if request.user and request.user.is_authenticated:
            return True
        return False


def is_uuid(value):
    try:
        return str(UUID(value))
    except:
        return None


# Test Utils
class TestUtil:
    def new_user():
        user_dict = {
            "first_name": "Test",
            "last_name": "Name",
            "email": "test@example.com",
            "password": "testpassword",
        }
        user = User.objects.create_user(**user_dict)
        return user

    def verified_user():
        user_dict = {
            "first_name": "Test",
            "last_name": "Verified",
            "email": "testverifieduser@example.com",
            "is_email_verified": True,
            "password": "testpassword",
        }
        user = User.objects.create_user(**user_dict)
        return user

    def another_verified_user():
        create_user_dict = {
            "first_name": "AnotherTest",
            "last_name": "UserVerified",
            "email": "anothertestverifieduser@example.com",
            "is_email_verified": True,
            "password": "anothertestverifieduser123",
        }
        user = User.objects.create_user(**create_user_dict)
        return user

    def auth_token(verified_user):
        access = Authentication.create_access_token({"user_id": str(verified_user.id)})
        refresh = Authentication.create_refresh_token()
        Jwt.objects.create(user_id=verified_user.id, access=access, refresh=refresh)
        return access
