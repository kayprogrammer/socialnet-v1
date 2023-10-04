"""
ASGI config for socialnet project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/asgi/
"""

import os
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
from decouple import config

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    f"socialnet.settings.{config('SETTINGS')}",
)

django_asgi_app = get_asgi_application()

from apps.chat.urls import chatsocket_urlpatterns
from apps.profiles.urls import notification_socket_urlpatterns
from apps.common.socket_auth import SocketAuthMiddleware

socket_urlpatterns = chatsocket_urlpatterns + notification_socket_urlpatterns

# AllowedHostsOriginValidator
application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        # Just HTTP for now. (We can add other protocols later.)
        "websocket": SocketAuthMiddleware(URLRouter(socket_urlpatterns)),
    }
)
