from django.urls import path

from . import views

urlpatterns = [
    path("", views.ProfilesView.as_view()),
    path("cities/", views.CitiesView.as_view()),
    path("profile/<str:username>/", views.ProfileView.as_view()),
    path("profile/", views.ProfileUpdateDeleteView.as_view()),
    path("friends/", views.FriendsView.as_view()),
    path("notifications/", views.NotificationsView.as_view()),
]
