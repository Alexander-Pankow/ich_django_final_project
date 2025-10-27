from django.urls import path

from .views import PopularSearchView


# URL pattern for retrieving top popular search queries from the last 30 days
# Эндпоинт для получения топ-10 популярных поисковых запросов за последние 30 дней
urlpatterns = [
    path("popular-search/", PopularSearchView.as_view(), name="popular-search"),
]