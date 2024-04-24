from django.urls import path
from .views import *
from rest_framework_simplejwt.views import TokenVerifyView


urlpatterns = [

    path("sign-up/", SignupView.as_view(), name="user-register"),
    path("<int:pk>/", AllUsersView.as_view(), name="users"),
    path("", AllUsersView.as_view(), name="users"),
    path("login/", LoginView.as_view(), name="token_obtain"),
    path("token/refresh/", LogoutView.as_view(), name="refresh_token"),
    path("verify/token/", TokenVerifyView.as_view(), name="token_verify"),
    path("change-phone/", ChangePhoneView.as_view(), name="change_phone"),
    path("verify/", VerifyView.as_view(), name="verify_confirmation_code"),
    path('change-password/', ChangePasswordView.as_view(), name='change_password'),
    path('password-reset/', PasswordResetAPIView.as_view(), name='password-reset'),
    path("password-reset/confirm/", PasswordResetConfirmAPIView.as_view(), name='password_reset_confirm'),
    path('resend/', ResendCodeAPIView.as_view(), name='code_resend'),
    path('check-password/', CheckUserPassword.as_view(), name='check-password'),
    path('profile/<int:pk>/',ProfileAPIView.as_view(), name='user_profile')
    # path('profile/',ListCreateProfileAPIView.as_view(), name='profile_list')


]