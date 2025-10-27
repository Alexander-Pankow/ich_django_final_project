from logging import getLogger
from typing import Any
from django.conf import settings
from django.core.mail import send_mail
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _

from apps.bookings.models import Booking
from apps.reviews.models import Review

logger = getLogger(__name__)


@receiver(post_save, sender=Booking)
def send_booking_notifications(sender: Any, instance: Booking, created: bool, **kwargs: Any) -> None:
    """
    Send email notifications when a booking is created or status is updated.

    Triggers:
    - On creation: notify tenant and landlord.
    - On status change to 'confirmed': notify tenant.
    - On status change to 'cancelled': notify both parties.
    """
    # Отправляет email-уведомления при создании или обновлении статуса бронирования

    try:
        if created:
            send_mail(
                subject=_("Your booking is confirmed — %(title)s") % {"title": instance.listing.title},  # Ваше бронирование подтверждено — %(title)s
                message=_("Hello, %(first_name)s!\n\n"
                          "You have successfully booked \"%(title)s\" "
                          "from %(start_date)s to %(end_date)s.\n\n"
                          "Thank you for using %(site_name)s!") % {
                    "first_name": instance.tenant.first_name,
                    "title": instance.listing.title,
                    "start_date": instance.start_date,
                    "end_date": instance.end_date,
                    "site_name": getattr(settings, 'SITE_NAME', 'our platform'),
                },
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[instance.tenant.email],
                fail_silently=False,
            )
            send_mail(
                subject=_("New booking — %(title)s") % {"title": instance.listing.title},  # Новое бронирование — %(title)s
                message=_("Hello, %(first_name)s!\n\n"
                          "User %(tenant_email)s has booked your listing "
                          "\"%(title)s\" from %(start_date)s to %(end_date)s.\n\n"
                          "Please confirm the booking in your dashboard.") % {
                    "first_name": instance.listing.owner.first_name,
                    "tenant_email": instance.tenant.email,
                    "title": instance.listing.title,
                    "start_date": instance.start_date,
                    "end_date": instance.end_date,
                },
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[instance.listing.owner.email],
                fail_silently=False,
            )

        elif instance.status == "confirmed" and "status" in (kwargs.get("update_fields") or []):
            send_mail(
                subject=_("Booking confirmed — %(title)s") % {"title": instance.listing.title},  # Бронирование подтверждено — %(title)s
                message=_("Hello, %(first_name)s!\n\n"
                          "The landlord has confirmed your booking "
                          "\"%(title)s\" from %(start_date)s to %(end_date)s.\n\n"
                          "Welcome!") % {
                    "first_name": instance.tenant.first_name,
                    "title": instance.listing.title,
                    "start_date": instance.start_date,
                    "end_date": instance.end_date,
                },
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[instance.tenant.email],
                fail_silently=False,
            )

        elif instance.status == "cancelled" and "status" in (kwargs.get("update_fields") or []):
            send_mail(
                subject=_("Booking cancelled"),  # Бронирование отменено
                message=_("Your booking for \"%(title)s\" has been cancelled.") % {"title": instance.listing.title},  # Ваше бронирование для "%(title)s" отменено.
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[instance.tenant.email],
                fail_silently=False,
            )
            send_mail(
                subject=_("Booking cancelled"),  # Бронирование отменено
                message=_("The booking for your listing \"%(title)s\" has been cancelled.") % {"title": instance.listing.title},  # Бронирование для вашего объявления "%(title)s" отменено.
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[instance.listing.owner.email],
                fail_silently=False,
            )

    except Exception as e:
        logger.error(f"Failed to send booking notification email: {e}", exc_info=True)


@receiver(post_save, sender=Review)
def send_review_notification(sender: Any, instance: Review, created: bool, **kwargs: Any) -> None:
    """
    Send email to landlord when a new review is posted.
    """
    # Отправляет email арендодателю при появлении нового отзыва

    if created:
        try:
            send_mail(
                subject=_("New review — %(title)s") % {"title": instance.listing.title},  # Новый отзыв — %(title)s
                message=_("Hello, %(first_name)s!\n\n"
                          "A tenant has left a review for your listing \"%(title)s\":\n\n"
                          "Rating: %(rating)s ★\n"
                          "Comment: %(comment)s\n\n"
                          "Thank you for your work!") % {
                    "first_name": instance.listing.owner.first_name,
                    "title": instance.listing.title,
                    "rating": instance.rating,
                    "comment": instance.comment,
                },
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[instance.listing.owner.email],
                fail_silently=False,
            )
        except Exception as e:
            logger.error(f"Failed to send review notification email: {e}", exc_info=True)