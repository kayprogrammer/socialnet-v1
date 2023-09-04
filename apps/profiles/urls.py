from django.urls import path

from . import views

urlpatterns = [
    path("profile/<str:username>/", views.ProfileView.as_view()),
]
