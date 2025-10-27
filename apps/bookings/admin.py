from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Booking


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    """
    Admin interface for managing Booking instances.

    Provides list display with tenant/listing info, filtering by status and dates,
    search by email/title/city, read-only price fields, and organized fieldsets.
    """
    # Админка бронирований: отображение, фильтрация, поиск, группировка полей

    list_display = (
        'tenant_email', 'listing_title', 'start_date', 'end_date',
        'check_in_time', 'check_out_time', 'status', 'total_price'
    )
    list_filter = ('status', 'is_deleted', 'start_date', 'end_date', 'listing__city')
    search_fields = (
        'tenant__email', 'listing__title', 'listing__city'
    )
    readonly_fields = ('total_price', 'created_at', 'updated_at')
    autocomplete_fields = ('listing', 'tenant')

    @admin.display(description=_('Tenant'), ordering='tenant__email')  # Арендатор
    def tenant_email(self, obj):
        """
        Returns the email of the booking's tenant.
        """
        # Возвращает email арендатора
        return obj.tenant.email

    @admin.display(description=_('Listing'), ordering='listing__title')  # Объявление
    def listing_title(self, obj):
        """
        Returns the title of the booked listing.
        """
        # Возвращает заголовок объявления
        return obj.listing.title

    fieldsets = (
        (_('Booking'), {  # Бронирование
            'fields': ('listing', 'tenant', 'status')
        }),
        (_('Dates and Times'), {  # Даты и время
            'fields': ('start_date', 'end_date', 'check_in_time', 'check_out_time')
        }),
        (_('Price'), {  # Цена
            'fields': ('total_price',)
        }),
        (_('System'), {  # Системные
            'fields': ('created_at', 'updated_at', 'is_deleted'),
            'classes': ('collapse',)
        }),
    )