from logging import getLogger
from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import OpenApiResponse, extend_schema, extend_schema_view
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError

from .models import Booking
from .serializers import BookingSerializer
from apps.common.permissions import IsTenant, IsBookingOwnerOrLandlord
from apps.common.validators import validate_booking_cancellation

logger = getLogger(__name__)


@extend_schema_view(
    get=extend_schema(
        summary=_("List bookings"),  # Список бронирований
        description=_("Returns user's bookings (tenant) or bookings for their listings (landlord)."),  # Возвращает бронирования пользователя (как арендатора) или бронирования его объявлений (как арендодателя)
        responses={200: BookingSerializer(many=True)},
    ),
    post=extend_schema(
        summary=_("Create booking"),  # Создание бронирования
        description=_("Create a new booking. Only tenants can book."),  # Создание нового бронирования. Бронировать могут только арендаторы
        request=BookingSerializer,
        responses={
            201: BookingSerializer,
            400: OpenApiResponse(description=_("Validation error")),  # Ошибка валидации
            403: OpenApiResponse(description=_("Only tenants allowed")),  # Разрешено только арендаторам
        },
    ),
)
class BookingListView(generics.ListCreateAPIView):
    """List and create bookings for authenticated users.

    Tenants can create new bookings.
    Both tenants and landlords can view their related bookings.
    """
    # Получение и создание бронирований: арендаторы — создают, все — просматривают свои

    serializer_class = BookingSerializer

    def get_queryset(self):
        """Return bookings related to the current user (as tenant or landlord)."""
        # Возвращает бронирования текущего пользователя (как арендатора или арендодателя)
        user = self.request.user
        tenant_bookings = Booking.objects.filter(is_deleted=False, tenant=user)
        landlord_bookings = Booking.objects.filter(is_deleted=False, listing__owner=user)
        return tenant_bookings.union(landlord_bookings)

    def get_permissions(self):
        """Apply IsTenant permission for POST, IsAuthenticated for GET."""
        # Назначает права: POST → только арендатор, GET → любой авторизованный
        if self.request.method == "POST":
            return [IsTenant()]
        return [permissions.IsAuthenticated()]

    def perform_create(self, serializer):
        """Save booking and log creation event."""
        # Сохраняет бронирование и логирует событие создания
        booking = serializer.save(tenant=self.request.user)
        logger.info(f"Booking {booking.id} created by tenant {self.request.user.id}")


@extend_schema_view(
    get=extend_schema(
        summary=_("Booking detail"),  # Детали бронирования
        description=_("Retrieve a single booking by ID."),  # Получение одного бронирования по ID
        responses={200: BookingSerializer},
    )
)
class BookingDetailView(generics.RetrieveAPIView):
    """Retrieve a single booking by ID with ownership validation."""
    # Получение одного бронирования с проверкой прав доступа

    queryset = Booking.objects.filter(is_deleted=False)
    serializer_class = BookingSerializer
    permission_classes = [IsBookingOwnerOrLandlord]


@extend_schema_view(
    patch=extend_schema(
        summary=_("Booking action"),  # Действие с бронированием
        description=_("Perform: cancel, confirm, reject. URL: /{id}/{action}/"),  # Выполнить: отмена, подтверждение, отказ. URL: /{id}/{action}/
        responses={
            200: BookingSerializer,
            400: OpenApiResponse(description=_("Invalid action or rule violation")),  # Недопустимое действие или нарушение правил
            403: OpenApiResponse(description=_("Permission denied")),  # Доступ запрещён
        },
    )
)
class BookingActionView(generics.UpdateAPIView):
    """Handle booking status changes via URL actions (cancel/confirm/reject)."""
    # Обработка изменений статуса бронирования через действия в URL

    queryset = Booking.objects.filter(is_deleted=False)
    serializer_class = BookingSerializer
    permission_classes = [IsBookingOwnerOrLandlord]

    def update(self, request, *args, **kwargs):
        """Process booking action (cancel/confirm/reject) based on URL parameter."""
        # Обрабатывает действие с бронированием (отмена/подтверждение/отказ)
        try:
            booking = self.get_object()
            action = self.kwargs.get("action")
            user = request.user

            if action == "cancel":
                if booking.tenant != user:
                    logger.warning(f"User {user.id} attempted to cancel booking {booking.id} without permission")
                    return Response(
                        {"error": _("Only the tenant can cancel the booking.")},
                        # Только арендатор может отменить бронирование
                        status=status.HTTP_403_FORBIDDEN
                    )
                validate_booking_cancellation(booking, user)
                booking.status = "cancelled"

            elif action == "confirm":
                if booking.listing.owner != user:
                    logger.warning(
                        f"User {user.id} attempted to confirm booking {booking.id} without being the landlord")
                    return Response(
                        {"error": _("Only the landlord can confirm the booking.")},
                        # Только арендодатель может подтвердить бронирование
                        status=status.HTTP_403_FORBIDDEN
                    )
                booking.status = "confirmed"

            elif action == "reject":
                if booking.listing.owner != user:
                    logger.warning(
                        f"User {user.id} attempted to reject booking {booking.id} without being the landlord")
                    return Response(
                        {"error": _("Only the landlord can reject the booking.")},
                        # Только арендодатель может отклонить бронирование
                        status=status.HTTP_403_FORBIDDEN
                    )
                booking.status = "cancelled"

            else:
                logger.warning(f"Invalid booking action '{action}' requested by user {user.id}")
                return Response(
                    {"error": _("Invalid action. Use: cancel, confirm, reject.")},
                    # Недопустимое действие. Используйте: cancel, confirm, reject
                    status=status.HTTP_400_BAD_REQUEST
                )

            booking.save(update_fields=["status"])
            logger.info(f"Booking {booking.id} status updated to '{booking.status}' by user {user.id}")
            return Response(self.get_serializer(booking).data)

        except ValidationError as e:
            logger.warning(f"Validation error in BookingActionView.update: {e.detail}")
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logger.error(f"Unexpected error in BookingActionView.update: {e}", exc_info=True)
            return Response(
                {"error": _("An internal error occurred while processing the request.")},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )