from django.urls import path

from . import views

urlpatterns = [
    path("posts/", views.PostsView.as_view()),
    path("posts/<slug:slug>/", views.PostDetailView.as_view()),
]
