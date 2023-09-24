from django.conf import settings
from apps.accounts.models import Jwt
from datetime import datetime, timedelta
import jwt, random, string

ALGORITHM = "HS256"


class Authentication:
    # generate random string
    def get_random(length: int):
        return "".join(random.choices(string.ascii_letters + string.digits, k=length))

    # generate access token based and encode user's id
    def create_access_token(payload: dict):
        expire = datetime.utcnow() + timedelta(
            minutes=int(settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        to_encode = {"exp": expire, **payload}
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    # generate random refresh token
    def create_refresh_token(
        expire=datetime.utcnow()
        + timedelta(minutes=int(settings.REFRESH_TOKEN_EXPIRE_MINUTES)),
    ):
        return jwt.encode(
            {"exp": expire, "data": Authentication.get_random(10)},
            settings.SECRET_KEY,
            algorithm=ALGORITHM,
        )

    # deocde access token from header
    def decode_jwt(token: str):
        try:
            decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        except:
            decoded = False
        return decoded

    def decodeAuthorization(token: str):
        decoded = Authentication.decode_jwt(token[7:])
        if not decoded:
            return None
        jwt_obj = Jwt.objects.select_related(
            "user",
            "user__city",
            "user__city__region",
            "user__city__country",
            "user__avatar",
        ).get_or_none(user_id=decoded["user_id"])
        if not jwt_obj:
            return None
        return jwt_obj.user
