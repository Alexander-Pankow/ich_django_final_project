from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    """
    Admin interface for managing user reviews on listings.
    """
    # Админка управления отзывами пользователей на объявления

    list_display = (
        'author_email', 'listing_title', 'rating', 'created_at'
    )
    list_filter = ('rating', 'is_deleted', 'created_at', 'booking__listing__city')
    search_fields = (
        'booking__tenant__email', 'booking__listing__title'
    )
    readonly_fields = ('created_at', 'updated_at', 'author_email', 'listing_title')
    autocomplete_fields = ('booking',)

    @admin.display(description=_('Author'))  # Автор
    def author_email(self, obj):
        """
        Display the email of the review author (tenant).
        """
        # Отображает email автора отзыва (арендатора)
        return obj.booking.tenant.email if obj.booking and obj.booking.tenant else '—'

    @admin.display(description=_('Listing'))  # Объявление
    def listing_title(self, obj):
        """
        Display the title of the reviewed listing.
        """
        # Отображает заголовок оценённого объявления
        return obj.booking.listing.title if obj.booking and obj.booking.listing else '—'

    fieldsets = (
        (_('Review'), {  # Отзыв
            'fields': ('booking', 'rating', 'comment')
        }),
        (_('Read-only relations'), {  # Связи (только для чтения)
            'fields': ('author_email', 'listing_title')
        }),
        (_('System'), {  # Системные
            'fields': ('created_at', 'updated_at', 'is_deleted'),
            'classes': ('collapse',)
        }),
    )