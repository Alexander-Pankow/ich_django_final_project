from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenBlacklistView

from .views import RegisterView, CurrentUserView


# Authentication URL patterns: register, login (JWT), logout (blacklist), and current user
# Эндпоинты аутентификации: регистрация, вход (JWT), выход (чёрный список), данные текущего пользователя
urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", TokenObtainPairView.as_view(), name="login"),
    path("logout/", TokenBlacklistView.as_view(), name="logout"),
    path("me/", CurrentUserView.as_view(), name="current-user"),
]