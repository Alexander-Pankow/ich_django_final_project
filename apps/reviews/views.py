from logging import getLogger
from drf_spectacular.utils import OpenApiResponse, extend_schema, extend_schema_view
from rest_framework import generics, permissions
from django.utils.translation import gettext_lazy as _

from .models import Review
from .serializers import ReviewSerializer
from apps.common.permissions import IsTenant

logger = getLogger(__name__)


@extend_schema_view(
    get=extend_schema(
        summary=_("List reviews for listing"),  # Список отзывов для объявления
        description=_("Public endpoint to get reviews for a specific listing."),  # Публичный эндпоинт для получения отзывов к конкретному объявлению
        responses={200: ReviewSerializer(many=True)},
    ),
    post=extend_schema(
        summary=_("Create review"),  # Создание отзыва
        description=_("Create a review for a listing. Only tenants with completed bookings can create reviews."),  # Создание отзыва к объявлению. Оставлять отзывы могут только арендаторы с завершёнными бронированиями
        request=ReviewSerializer,
        responses={
            201: ReviewSerializer,
            400: OpenApiResponse(description=_("Validation error (e.g., no completed booking)")),  # Ошибка валидации (например, нет завершённого бронирования)
            403: OpenApiResponse(description=_("Only tenants can create reviews")),  # Отзывы могут оставлять только арендаторы
        },
    ),
)
class ReviewListView(generics.ListCreateAPIView):
    """
    List and create reviews for a listing.
    """
    # Получение и создание отзывов для объявления

    serializer_class = ReviewSerializer

    def get_permissions(self):
        """
        Set permissions: POST → IsTenant, GET → AllowAny.
        """
        # Назначает права: POST → арендатор, GET → все
        if self.request.method == "POST":
            return [IsTenant()]
        return [permissions.AllowAny()]

    def get_queryset(self):
        """
        Return non-deleted reviews for the specified listing.
        """
        # Возвращает неудалённые отзывы для указанного объявления
        return Review.objects.filter(
            booking__listing_id=self.kwargs["listing_id"],
            is_deleted=False,
        ).select_related("booking__listing", "booking__tenant")

    def perform_create(self, serializer):
        """
        Save review and log creation event.
        """
        # Сохраняет отзыв и логирует событие создания
        review = serializer.save()
        logger.info(f"Review {review.id} created by tenant {review.booking.tenant.id} for listing {review.booking.listing.id}")