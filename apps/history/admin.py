from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import SearchQuery, ViewHistory


@admin.register(SearchQuery)
class SearchQueryAdmin(admin.ModelAdmin):
    """
    Admin interface for search query history.
    """
    # Админка истории поисковых запросов

    list_display = ('user_email', 'query', 'created_at')
    list_filter = ('created_at', 'is_deleted')
    search_fields = ('query', 'user__email')
    readonly_fields = ('created_at', 'updated_at')
    autocomplete_fields = ('user',)

    @admin.display(description=_('User'))  # Пользователь
    def user_email(self, obj):
        """
        Display user email or 'Anonymous' if user is deleted.
        """
        # Отображает email пользователя или 'Аноним', если пользователь удалён
        return obj.user.email if obj.user else _('Anonymous')  # Аноним


@admin.register(ViewHistory)
class ViewHistoryAdmin(admin.ModelAdmin):
    """
    Admin interface for listing view history.
    """
    # Админка истории просмотров объявлений

    list_display = ('user_email', 'listing_title', 'created_at')
    list_filter = ('created_at', 'is_deleted', 'listing__city')
    search_fields = ('user__email', 'listing__title')
    readonly_fields = ('created_at', 'updated_at')
    autocomplete_fields = ('listing', 'user')

    @admin.display(description=_('User'))  # Пользователь
    def user_email(self, obj):
        """
        Display user email or 'Anonymous' if user is deleted.
        """
        # Отображает email пользователя или 'Аноним', если пользователь удалён
        return obj.user.email if obj.user else _('Anonymous')  # Аноним

    @admin.display(description=_('Listing'))  # Объявление
    def listing_title(self, obj):
        """
        Display the title of the viewed listing.
        """
        # Отображает заголовок просмотренного объявления
        return obj.listing.title if obj.listing else _('Deleted listing')