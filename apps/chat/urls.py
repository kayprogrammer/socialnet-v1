from django.urls import path

from . import views

urlpatterns = [
    path("", views.ChatsView.as_view()),
    path("<uuid:chat_id>/", views.ChatView.as_view()),
]
