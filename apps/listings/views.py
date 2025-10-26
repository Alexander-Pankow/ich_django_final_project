from logging import getLogger
from django.db.models import Count, Q
from drf_spectacular.utils import OpenApiResponse, extend_schema, extend_schema_view
from rest_framework import generics, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from django.utils.translation import gettext_lazy as _

from .models import Listing
from .serializers import ListingSerializer
from apps.common.permissions import IsLandlord, IsOwner
from apps.history.models import SearchQuery, ViewHistory
from .filters import ListingFilter

logger = getLogger(__name__)


@extend_schema_view(
    get=extend_schema(
        summary=_("List listings"),  # Список объявлений
        description=_("Public endpoint to list active listings with filtering and search."),  # Публичный эндпоинт для просмотра активных объявлений с фильтрацией и поиском
        parameters=[
            ("search", _("Search in title/description"), "query", str, False),  # Поиск в заголовке/описании
            ("price_min", _("Minimum price"), "query", float, False),  # Минимальная цена
            ("price_max", _("Maximum price"), "query", float, False),  # Максимальная цена
            ("rooms_min", _("Minimum rooms"), "query", int, False),  # Минимум комнат
            ("rooms_max", _("Maximum rooms"), "query", int, False),  # Максимум комнат
            ("housing_type", _("Housing type"), "query", str, False),  # Тип жилья
            ("city", _("City name"), "query", str, False),  # Название города
        ],
        responses={200: ListingSerializer(many=True)},
    ),
    post=extend_schema(
        summary=_("Create listing"),  # Создание объявления
        description=_("Create a new listing. Only landlords can create listings."),  # Создание нового объявления. Создавать могут только арендодатели
        request=ListingSerializer,
        responses={
            201: ListingSerializer,
            400: OpenApiResponse(description=_("Validation error")),  # Ошибка валидации
            403: OpenApiResponse(description=_("Only landlords allowed")),  # Разрешено только арендодателям
        },
    ),
)
class ListingListView(generics.ListCreateAPIView):
    """List active listings publicly or create a new listing (landlords only).

    Supports search, filtering by price/rooms/type/city, and ordering.
    On search, saves query to history for authenticated users.
    """
    # Получение активных объявлений (публично) или создание (только арендодатели); поддержка поиска, фильтрации, сортировки
    queryset = Listing.objects.filter(is_active=True, is_deleted=False)
    serializer_class = ListingSerializer
    filter_backends = [filters.OrderingFilter, DjangoFilterBackend]
    filterset_class = ListingFilter
    ordering_fields = ["price", "created_at"]
    ordering = ["-created_at"]

    def get_permissions(self):
        """Allow anyone to list; restrict creation to landlords."""
        # Разрешает всем просматривать; создание — только арендодателям
        if self.request.method == "POST":
            return [IsLandlord()]
        return [permissions.AllowAny()]

    def get_queryset(self):
        """Return active, non-deleted listings."""
        # Всё фильтруется автоматически через ListingFilter
        return Listing.objects.filter(is_active=True, is_deleted=False)

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)

        search = request.query_params.get("search")
        if search and request.user.is_authenticated:
            try:
                SearchQuery.objects.get_or_create(user=request.user, query=search)
                logger.info(f"Saved search query '{search}' for user {request.user.id}")
            except Exception as e:
                logger.error(f"Failed to save search query: {e}")

        return response

    def perform_create(self, serializer):
        """Assign the current user as the listing owner and log the event."""
        # Назначает текущего пользователя владельцем объявления и логирует событие
        listing = serializer.save(owner=self.request.user)
        logger.info(f"Listing {listing.id} created by landlord {self.request.user.id}")


@extend_schema_view(
    get=extend_schema(
        summary=_("Listing detail"),  # Детали объявления
        description=_("Get listing by ID. Public access."),  # Получение объявления по ID. Публичный доступ
        responses={200: ListingSerializer},
    ),
    put=extend_schema(
        summary=_("Update listing"),  # Обновление объявления
        description=_("Update listing. Only owner can update."),  # Обновление объявления. Только владелец может редактировать
        request=ListingSerializer,
        responses={
            200: ListingSerializer,
            403: OpenApiResponse(description=_("Only owner can update")),  # Только владелец может обновлять
        },
    ),
    patch=extend_schema(
        summary=_("Partial update listing"),  # Частичное обновление
        description=_("Partially update listing. Only owner can update."),  # Частичное обновление. Только владелец
        request=ListingSerializer,
        responses={
            200: ListingSerializer,
            403: OpenApiResponse(description=_("Only owner can update")),  # Только владелец может обновлять
        },
    ),
    delete=extend_schema(
        summary=_("Delete listing"),  # Удаление объявления
        description=_("Soft delete listing. Only owner can delete."),  # Мягкое удаление. Только владелец может удалить
        responses={204: None, 403: OpenApiResponse(description=_("Only owner can delete"))},  # Только владелец может удалять
    ),
)
class ListingDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or soft-delete a listing with ownership validation."""
    # Получение, обновление или мягкое удаление объявления с проверкой прав

    queryset = Listing.objects.filter(is_deleted=False)
    serializer_class = ListingSerializer

    def get_permissions(self):
        """Allow public read; restrict write operations to the owner."""
        # Чтение — публичное; запись — только владельцу
        if self.request.method in ["PUT", "PATCH", "DELETE"]:
            return [IsOwner()]
        return [permissions.AllowAny()]

    def retrieve(self, request, *args, **kwargs):
        """Record view in history for authenticated users."""
        # Записывает просмотр в историю для авторизованных пользователей
        instance = self.get_object()
        if request.user.is_authenticated:
            try:
                ViewHistory.objects.get_or_create(user=request.user, listing=instance)
                logger.info(f"User {request.user.id} viewed listing {instance.id}")
            except Exception as e:
                logger.error(f"Failed to record view for user {request.user.id}, listing {instance.id}: {e}")
        return super().retrieve(request, *args, **kwargs)


@extend_schema_view(
    get=extend_schema(
        summary=_("Popular listings"),  # Популярные объявления
        description=_("Get top 10 most viewed listings."),  # Получение топ-10 самых просматриваемых объявлений
        responses={200: ListingSerializer(many=True)},
    )
)
class PopularListingsView(generics.ListAPIView):
    """Return the 10 most viewed active listings."""
    # Возвращает 10 самых популярных активных объявлений по количеству просмотров

    serializer_class = ListingSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        """Annotate and order listings by view count, limit to top 10."""
        # Аннотирует и сортирует объявления по количеству просмотров, ограничивает до 10
        return (
            Listing.objects.filter(is_active=True, is_deleted=False)
            .annotate(views_count=Count("viewhistory"))
            .order_by("-views_count")[:10]
        )