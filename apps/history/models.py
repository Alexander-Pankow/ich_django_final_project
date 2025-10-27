from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from apps.common.models import BaseModel
from apps.listings.models import Listing


class SearchQuery(BaseModel):
    """
    Represents a search query made by a user (or anonymous).
    """
    # Представляет поисковый запрос, сделанный пользователем (или анонимом)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('User')  # Пользователь
    )
    query = models.CharField(
        _('Search query'),  # Поисковый запрос
        max_length=255
    )

    class Meta:
        verbose_name = _('Search query')  # Поисковый запрос
        verbose_name_plural = _('Search history')  # История поиска
        ordering = ['-created_at']

    def __str__(self):
        user = self.user.email if self.user else _("Anonymous")  # Аноним
        return f"{user}: {self.query}"


class ViewHistory(BaseModel):
    """
    Records when a user views a listing.
    """
    # Фиксирует факт просмотра объявления пользователем

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('User')  # Пользователь
    )
    listing = models.ForeignKey(
        Listing,
        on_delete=models.CASCADE,
        verbose_name=_('Listing')  # Объявление
    )

    class Meta:
        verbose_name = _('Listing view')  # Просмотр объявления
        verbose_name_plural = _('View history')  # История просмотров
        ordering = ['-created_at']

    def __str__(self):
        user = self.user.email if self.user else _("Anonymous")  # Аноним
        listing_title = self.listing.title if self.listing else _("Deleted listing")  # Удалённое объявление
        return f"{user} → {listing_title}"