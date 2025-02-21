from django.urls import path

from apps.chat import consumers

from . import views

urlpatterns = [
    path("", views.ChatsView.as_view()),
    path("<uuid:chat_id>/", views.ChatView.as_view()),
    path("messages/<uuid:message_id>/", views.MessageView.as_view()),
    path("groups/group/", views.ChatGroupCreateView.as_view()),
]

chatsocket_urlpatterns = [
    path("api/v1/ws/chats/<str:id>/", consumers.ChatConsumer.as_asgi())
]
