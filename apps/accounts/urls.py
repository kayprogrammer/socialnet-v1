from django.urls import path

from . import views

urlpatterns = [
    path("register/", views.RegisterView.as_view()),
    path("verify-email/", views.VerifyEmailView.as_view()),
]
