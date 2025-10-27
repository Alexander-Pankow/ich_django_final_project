from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import OpenApiResponse, extend_schema, extend_schema_view
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from .serializers import RegisterSerializer, UserSerializer


@extend_schema_view(
    post=extend_schema(
        summary=_("Register user"),  # Регистрация пользователя
        description=_("Register a new user (tenant or landlord)."),  # Регистрация нового пользователя (арендатора или арендодателя)
        request=RegisterSerializer,
        responses={
            201: UserSerializer,
            400: OpenApiResponse(description=_("Validation error (e.g., password mismatch, email exists)")),  # Ошибка валидации (например, несовпадение паролей, email уже существует)
        },
    ),
)
class RegisterView(generics.CreateAPIView):
    """
    Register a new user.
    """
    # Регистрация нового пользователя

    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        """
        Handle user registration and return user data without password.
        """
        # Обрабатывает регистрацию пользователя и возвращает данные без пароля
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


@extend_schema_view(
    get=extend_schema(
        summary=_("Current user"),  # Текущий пользователь
        description=_("Get details of the authenticated user."),  # Получение данных авторизованного пользователя
        responses={200: UserSerializer},
    ),
)
class CurrentUserView(generics.RetrieveAPIView):
    """
    Retrieve current user details.
    """
    # Получение данных текущего пользователя

    serializer_class = UserSerializer

    def get_object(self):
        """
        Return the currently authenticated user.
        """
        # Возвращает текущего авторизованного пользователя
        return self.request.user