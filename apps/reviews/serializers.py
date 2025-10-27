from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from .models import Review
from apps.common.validators import validate_booking_for_review


class ReviewSerializer(serializers.ModelSerializer):
    """
    Serializer for creating and viewing reviews on completed bookings.
    """
    # Сериализатор для создания и просмотра отзывов по завершённым бронированиям

    author_name = serializers.CharField(
        source='author.get_full_name',
        read_only=True
    )
    listing_title = serializers.CharField(
        source='listing.title',
        read_only=True
    )

    class Meta:
        model = Review
        fields = (
            'id', 'booking', 'listing_title', 'author_name',
            'rating', 'comment', 'created_at'
        )
        read_only_fields = ('created_at',)

    def validate_booking(self, value):
        """
        Validate that the user can review this booking.
        """
        # Проверяет, что пользователь может оставить отзыв на это бронирование
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            raise serializers.ValidationError(_("Authentication required."))  # Требуется авторизация.

        if value.tenant != request.user:
            raise serializers.ValidationError(
                _("You can only review your own bookings.")  # Вы можете оставить отзыв только на своё бронирование.
            )

        validate_booking_for_review(value)
        return value