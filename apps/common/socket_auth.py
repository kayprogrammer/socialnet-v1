import json

from django.conf import settings
from apps.accounts.auth import Authentication
from asgiref.sync import sync_to_async


class SocketAuthMiddleware:
    """
    Custom middleware that verifies the user.
    """

    def __init__(self, app):
        # Store the ASGI application we were passed
        self.app = app

    async def __call__(self, scope, receive, send):
        headers = {key.decode(): value.decode() for key, value in scope["headers"]}
        token = headers.get("authorization")
        error = {"type": "auth"}
        if not token:
            error["message"] = "Auth bearer not set"
        else:
            if (
                token == settings.SOCKET_SECRET
            ):  # If the app is making the connection itself
                scope["user"] = token
            else:
                user = await sync_to_async(Authentication.decodeAuthorization)(token)
                scope["user"] = user
                if not user:
                    error["message"] = "Auth token is invalid or expired"

        scope["error"] = error
        return await self.app(scope, receive, send)
