from django.urls import path

from . import views

urlpatterns = [
    path("cities/", views.CitiesView.as_view()),
    path("profile/<str:username>/", views.ProfileView.as_view()),
    path("profile/", views.ProfileUpdateDeleteView.as_view()),
]
