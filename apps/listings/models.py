import re
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from apps.common.models import BaseModel
from .choices import HOUSING_TYPE_CHOICES
from apps.common.validators import validate_price_range, validate_min_rooms


class Listing(BaseModel):
    """
    Represents a housing listing in Germany with full metadata and validation.
    """
    # Представляет объявление о жилье в Германии с полными метаданными и валидацией

    title = models.CharField(
        _('Title'),  # Заголовок
        max_length=255
    )
    description = models.TextField(
        _('Description'),  # Описание
        max_length=15000
    )
    street = models.CharField(
        _('Street and house number'),  # Улица и номер дома
        max_length=255,
        blank=True
    )
    city = models.CharField(
        _('City'),  # Город
        max_length=100
    )
    postal_code = models.CharField(
        _('Postal code'),  # Почтовый индекс
        max_length=10,
        blank=True
    )
    price = models.DecimalField(
        _('Price'),  # Цена
        max_digits=10,
        decimal_places=2,
        validators=[validate_price_range]
    )
    rooms = models.PositiveSmallIntegerField(
        _('Number of rooms'),  # Количество комнат
        validators=[validate_min_rooms]
    )
    housing_type = models.CharField(
        _('Housing type'),  # Тип жилья
        max_length=20,
        choices=HOUSING_TYPE_CHOICES
    )
    is_active = models.BooleanField(
        _('Active'),  # Активно
        default=True
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        verbose_name=_('Owner'),  # Владелец
        related_name='listings'
    )

    class Meta:
        verbose_name = _('Listing')  # Объявление
        verbose_name_plural = _('Listings')  # Объявления
        ordering = ['-created_at']

    def clean(self):
        """
        Validate business rules specific to German housing listings.
        """
        # Валидация бизнес-правил для объявлений о жилье в Германии

        if self.postal_code:
            if not re.fullmatch(r'\d{5}', self.postal_code):
                raise ValidationError({
                    'postal_code': _("German postal code must be exactly 5 digits.")
                    # Немецкий почтовый индекс должен состоять ровно из 5 цифр.
                })

        if self.city and not self.city.strip():
            raise ValidationError({
                'city': _("City name cannot be empty.")
                # Название города не может быть пустым.
            })

    def save(self, *args, **kwargs):
        """
        Ensure model validation is always performed before saving.
        """
        # Гарантирует выполнение валидации перед сохранением
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} ({self.city}) — {self.price} €"