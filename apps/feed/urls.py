from django.urls import path

from . import views

urlpatterns = [
    path("posts/", views.PostsView.as_view()),
    path("posts/<slug:slug>/", views.PostDetailView.as_view()),
    path("posts/<slug:slug>/comments/", views.CommentsView.as_view()),
    path("comments/<slug:slug>/", views.CommentView.as_view()),
    path("replies/<slug:slug>/", views.ReplyView.as_view()),
    path("reactions/<str:focus>/<slug:slug>/", views.ReactionsView.as_view()),
    path("reactions/<uuid:id>/", views.RemoveReaction.as_view()),
]
