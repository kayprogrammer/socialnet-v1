from django.urls import path

from . import views

urlpatterns = [
    path("register/", views.RegisterView.as_view()),
    path("verify-email/", views.VerifyEmailView.as_view()),
    path("resend-verification-email/", views.ResendVerificationEmailView.as_view()),
    path("send-password-reset-otp/", views.SendPasswordResetOtpView.as_view()),
    path("set-new-password/", views.SetNewPasswordView.as_view()),
    path("login/", views.LoginView.as_view()),
    path("refresh/", views.RefreshTokensView.as_view()),
    path("logout/", views.LogoutView.as_view()),
]
