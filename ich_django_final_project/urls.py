"""
URL configuration for ich_django_final_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
"""

from django.contrib import admin
from django.urls import path, include
from django.conf.urls.i18n import i18n_patterns
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView


# API schema and documentation (language-independent)
# Схема API и документация (не зависят от языка)
urlpatterns = [

    path('', include('apps.common.urls')),  # главная страница
]

# Localized URL patterns (admin and API endpoints)
# Локализованные маршруты (админка и API)
urlpatterns += i18n_patterns(
    path('admin/', admin.site.urls),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/v1/users/', include('apps.users.urls')),
    path('api/v1/listings/', include('apps.listings.urls')),
    path('api/v1/bookings/', include('apps.bookings.urls')),
    path('api/v1/', include('apps.reviews.urls')),
    path('api/v1/search-history/', include('apps.history.urls')),
)