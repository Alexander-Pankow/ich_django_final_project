from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from apps.common.models import BaseModel
from apps.listings.models import Listing
from apps.bookings.choices import BOOKING_STATUS_CHOICES
from apps.common.validators import (
    validate_future_date,
    validate_end_date_after_start,
    validate_booking_duration,
    validate_no_overlapping_booking,
    validate_not_own_listing,
)


class Booking(BaseModel):
    """Represents a booking of a listing by a tenant for a specific period.

    Includes validation for date ranges, ownership, overlapping bookings,
    and automatic total price calculation based on listing price and duration.
    """
    # Модель бронирования жилья: валидация дат, расчёт цены, защита от пересечений и бронирования своего объявления

    listing = models.ForeignKey(
        Listing,
        on_delete=models.PROTECT,
        verbose_name=_('Listing'),  # Объявление
        related_name='bookings'
    )
    tenant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        verbose_name=_('Tenant'),  # Арендатор
        related_name='bookings'
    )
    start_date = models.DateField(
        _('Start date'),  # Дата начала
        validators=[validate_future_date]
    )
    end_date = models.DateField(
        _('End date')  # Дата окончания
    )
    check_in_time = models.TimeField(
        _('Check-in time'),  # Время заезда
        default='14:00'
    )
    check_out_time = models.TimeField(
        _('Check-out time'),  # Время выезда
        default='12:00'
    )
    total_price = models.DecimalField(
        _('Total price'),  # Итоговая цена
        max_digits=10,
        decimal_places=2,
        editable=False
    )
    status = models.CharField(
        _('Status'),  # Статус
        max_length=20,
        choices=BOOKING_STATUS_CHOICES,
        default='pending'
    )

    def clean(self):
        """Performs business logic validation before saving the booking.

        Validates:
        - end date is after start date,
        - booking duration is within allowed limits,
        - tenant is not booking their own listing,
        - no overlapping bookings for the same listing,
        - tenant and listing cannot be changed after creation.

        Raises:
            ValidationError: if any business rule is violated.
        """
        # Выполняет валидацию бизнес-логики: даты, длительность, пересечения, запрет изменения арендатора/объявления

        if self.start_date and self.end_date:
            validate_end_date_after_start(self.start_date, self.end_date)
            validate_booking_duration(self.start_date, self.end_date)
            if self.tenant and self.listing:
                validate_not_own_listing(self.tenant, self.listing)
                if self.pk is not None:
                    old = Booking.objects.filter(pk=self.pk).first()
                    if old:
                        if old.tenant != self.tenant:
                            raise ValidationError(
                                _("Cannot change tenant after booking is created.")  # Нельзя изменить арендатора после создания бронирования.
                            )
                        if old.listing != self.listing:
                            raise ValidationError(
                                _("Cannot change listing after booking is created.")  # Нельзя изменить объявление после создания бронирования.
                            )
                        if old.start_date != self.start_date or old.end_date != self.end_date:
                            validate_no_overlapping_booking(
                                self.listing, self.start_date, self.end_date, exclude_id=self.pk
                            )
                else:
                    validate_no_overlapping_booking(self.listing, self.start_date, self.end_date)

    def save(self, *args, **kwargs):
        """Saves the booking instance to the database.

        Automatically recalculates total_price if start_date or end_date changes.
        Runs full_clean() unless skip_validation=True is passed.

        Args:
            skip_validation (bool): if True, skips model validation (default: False).
            *args: positional arguments passed to parent save().
            **kwargs: keyword arguments (e.g., update_fields) passed to parent save().
        """
        # Сохраняет бронирование; пересчитывает total_price при изменении дат; запускает валидацию

        skip_validation = kwargs.pop('skip_validation', False)
        if not skip_validation:
            self.full_clean()

        should_recalculate = (
            self.pk is None or
            (kwargs.get('update_fields') and
             any(f in kwargs['update_fields'] for f in ['start_date', 'end_date']))
        )
        if should_recalculate:
            days = (self.end_date - self.start_date).days
            self.total_price = self.listing.price * days

        super().save(*args, **kwargs)

    class Meta:
        verbose_name = _('Booking')  # Бронирование
        verbose_name_plural = _('Bookings')  # Бронирования
        ordering = ['-created_at']

    def __str__(self):
        return f"Booking by {self.tenant.email} for {self.listing.title} ({self.start_date}–{self.end_date})"
