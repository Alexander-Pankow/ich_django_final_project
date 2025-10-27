from typing import Any, Dict

from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from .models import Booking
from apps.common.validators import (
    validate_not_own_listing,
    validate_no_overlapping_booking,
    validate_end_date_after_start,
    validate_booking_duration,
)


class BookingSerializer(serializers.ModelSerializer):
    """
    Serializer for creating and viewing booking instances.

    On creation, tenant is set automatically from the request user.
    Date and time fields become read-only after booking is created.
    Applies business rule validation via shared validators.
    """
    # Сериализатор для создания и просмотра бронирований: автоматически назначает арендатора, блокирует даты после создания, применяет валидацию

    listing_title = serializers.CharField(source="listing.title", read_only=True)

    class Meta:
        model = Booking
        fields = (
            "id",
            "listing",
            "listing_title",
            "start_date",
            "end_date",
            "check_in_time",
            "check_out_time",
            "total_price",
            "status",
            "created_at",
        )
        read_only_fields = ("tenant", "total_price", "status", "created_at")

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """
        Make date/time fields read-only if instance exists (i.e., on update).
        """
        # Делает поля даты/времени только для чтения, если объект уже существует (при обновлении)
        super().__init__(*args, **kwargs)
        if self.instance:
            for field in ["start_date", "end_date", "check_in_time", "check_out_time"]:
                self.fields[field].read_only = True

    def validate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate booking against business rules using shared validators.

        Checks:
        - user is authenticated,
        - end date > start date,
        - booking duration within limits,
        - user is not booking own listing,
        - no overlapping bookings exist.

        Args:
            data: validated input data.

        Returns:
            Validated data dict.

        Raises:
            serializers.ValidationError: if any rule is violated.
        """
        # Валидация бронирования: авторизация, даты, длительность, запрет бронирования своего жилья, отсутствие пересечений
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            raise serializers.ValidationError(_("Authentication required."))  # Требуется авторизация.

        user = request.user
        start = data["start_date"]
        end = data["end_date"]
        listing = data["listing"]

        validate_end_date_after_start(start, end)
        validate_booking_duration(start, end)
        validate_not_own_listing(user, listing)
        validate_no_overlapping_booking(listing, start, end)

        return data

    def create(self, validated_data: Dict[str, Any]) -> Booking:
        """
        Create a new booking with tenant set from the current request user.
        """
        # Создаёт новое бронирование с арендатором из контекста запроса
        validated_data["tenant"] = self.context["request"].user
        return super().create(validated_data)