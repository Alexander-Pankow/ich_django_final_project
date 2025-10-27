from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _

from apps.common.models import BaseModel
from apps.bookings.models import Booking
from apps.common.validators import validate_booking_for_review


class Review(BaseModel):
    """
    Represents a tenant's review and rating for a completed booking.
    """
    # Представляет отзыв и рейтинг арендатора по завершённому бронированию

    booking = models.OneToOneField(
        Booking,
        on_delete=models.CASCADE,
        related_name='review',
        verbose_name=_('Booking')  # Бронирование
    )
    rating = models.PositiveSmallIntegerField(
        _('Rating'),  # Рейтинг
        validators=[
            MinValueValidator(1, message=_("Rating must be between 1 and 5.")),  # Рейтинг должен быть от 1 до 5.
            MaxValueValidator(5, message=_("Rating must be between 1 and 5."))   # Рейтинг должен быть от 1 до 5.
        ]
    )
    comment = models.TextField(
        _('Comment')  # Комментарий
    )

    @property
    def listing(self):
        """
        Return the listing associated with this review.
        """
        # Возвращает объявление, связанное с этим отзывом
        return self.booking.listing if self.booking else None

    @property
    def author(self):
        """
        Return the tenant who wrote the review.
        """
        # Возвращает арендатора, оставившего отзыв
        return self.booking.tenant if self.booking else None

    def clean(self):
        """
        Validate that the booking is eligible for a review.
        """
        # Проверяет, что бронирование можно оценить (завершено и в прошлом)
        if self.booking:
            validate_booking_for_review(self.booking)

    def save(self, *args, **kwargs):
        """
        Ensure model validation is performed before saving.
        """
        # Гарантирует выполнение валидации перед сохранением
        self.full_clean()
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = _('Review')  # Отзыв
        verbose_name_plural = _('Reviews')  # Отзывы
        ordering = ['-created_at']

    def __str__(self):
        if self.booking and self.booking.tenant and self.booking.listing:
            return f"Review by {self.booking.tenant.email} on “{self.booking.listing.title}” ({self.rating})"
        return f"Review (ID: {self.pk}) – orphaned"