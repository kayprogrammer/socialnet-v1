from django.urls import path

from . import views

urlpatterns = [
    path("", views.ChatsView.as_view()),
]
