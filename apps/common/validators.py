from rest_framework.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal


def validate_future_date(value):
    """Ensure the date is not in the past."""
    # Проверяет, что дата не в прошлом
    if value < timezone.now().date():
        raise ValidationError(_("Date cannot be in the past."))  # Нельзя использовать дату из прошлого.


def validate_price_range(value, min_price=Decimal('10.00'), max_price=Decimal('10000.00')):
    """Validate that nightly price is within allowed range."""
    # Проверка диапазона цены за ночь
    if value < min_price:
        raise ValidationError(
            _("Minimum price is %(min)s €.") % {'min': min_price}  # Минимальная цена — %(min)s €.
        )
    if value > max_price:
        raise ValidationError(
            _("Maximum price is %(max)s €.") % {'max': max_price}  # Максимальная цена — %(max)s €.
        )


def validate_min_rooms(value):
    """Ensure number of rooms is at least 1."""
    # Проверяет, что комнат хотя бы 1
    if value < 1:
        raise ValidationError(_("Number of rooms must be at least 1."))  # Количество комнат должно быть >= 1.


def validate_end_date_after_start(start_date, end_date):
    """Ensure end date is strictly after start date."""
    # Проверяет, что дата окончания позже начала
    if end_date <= start_date:
        raise ValidationError(
            _("End date must be after start date.")  # Дата окончания должна быть позже даты начала.
        )


def validate_booking_duration(start_date, end_date, min_nights=1, max_nights=365):
    """Validate booking duration is within allowed limits."""
    # Проверка минимального и максимального срока бронирования
    nights = (end_date - start_date).days
    if nights < min_nights:
        raise ValidationError(
            _("Minimum booking duration is %(min)s nights.") % {'min': min_nights}  # Минимальный срок бронирования — %(min)s ночей.
        )
    if nights > max_nights:
        raise ValidationError(
            _("Maximum booking duration is %(max)s nights.") % {'max': max_nights}  # Максимальный срок бронирования — %(max)s ночей.
        )


def validate_no_overlapping_booking(listing, start_date, end_date, exclude_id=None):
    """Ensure no active overlapping bookings exist for the listing."""
    # Проверяет, что нет пересекающихся активных бронирований
    from apps.bookings.models import Booking
    overlapping = Booking.objects.filter(
        listing=listing,
        status__in=['pending', 'confirmed'],
        start_date__lt=end_date,
        end_date__gt=start_date
    )
    if exclude_id:
        overlapping = overlapping.exclude(pk=exclude_id)
    if overlapping.exists():
        raise ValidationError(
            _("This property is already booked for the selected dates.")  # Это жильё уже забронировано на выбранные даты.
        )


def validate_not_own_listing(user, listing):
    """Prevent users from booking their own listings."""
    # Проверяет, что пользователь не бронирует своё жильё
    if listing.owner == user:
        raise ValidationError(
            _("You cannot book your own listing.")  # Вы не можете забронировать своё собственное жильё.
        )


def validate_booking_for_review(booking):
    """Ensure booking is eligible for review: confirmed/completed and ended."""
    # Проверяет, что можно оставить отзыв: статус подтверждён/завершён и дата окончания в прошлом
    if booking.status not in ['confirmed', 'completed']:
        raise ValidationError(
            _("Reviews can only be left for confirmed or completed bookings.")  # Можно оставлять отзыв только по подтверждённым или завершённым бронированиям.
        )

    if timezone.now().date() < booking.end_date:
        raise ValidationError(
            _("You cannot leave a review before the stay ends.")  # Нельзя оставить отзыв до окончания срока проживания.
        )


def validate_booking_cancellation(booking, user):
    """Validate that tenant can cancel booking at least 7 days before start."""
    # Проверяет, что отмена возможна не позже чем за 7 дней до заезда

    if booking.tenant != user:
        raise ValidationError(
            {"detail": _("Only the tenant can cancel this booking.")}  # Только арендатор может отменить это бронирование.
        )

    today = timezone.now().date()
    if booking.start_date < today + timedelta(days=7):
        raise ValidationError(
            {"detail": _("Cancellation is only allowed at least 7 days before the start date.")}  # Отмена разрешена только минимум за 7 дней до даты заезда.
        )