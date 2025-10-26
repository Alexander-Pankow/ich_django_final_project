from datetime import timedelta
from django.test import TestCase
from django.contrib.auth.models import Group
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework import status
from .models import SearchQuery, ViewHistory
from apps.users.models import User
from apps.listings.models import Listing


class HistoryModelTest(TestCase):
    """Tests for history models (SearchQuery and ViewHistory)."""

    def setUp(self):
        Group.objects.get_or_create(name="Tenants")
        self.user = User.objects.create_user(
            email="user@example.com",
            first_name="User",
            password="pass123"
        )
        self.user.groups.add(Group.objects.get(name="Tenants"))

        self.listing = Listing.objects.create(
            owner=self.user,
            title="Test Listing",
            description="Test",
            city="Berlin",
            price=1000,
            rooms=1,
            housing_type="apartment"
        )

    def test_search_query_creation(self):
        """Test creating a search query."""
        query = SearchQuery.objects.create(user=self.user, query="central")
        self.assertEqual(query.query, "central")
        self.assertEqual(query.user, self.user)

    def test_view_history_creation(self):
        """Test creating a view history record."""
        view = ViewHistory.objects.create(user=self.user, listing=self.listing)
        self.assertEqual(view.user, self.user)
        self.assertEqual(view.listing, self.listing)


class PopularSearchViewTest(APITestCase):
    """Тесты популярных поисковых запросов."""

    def setUp(self):
        Group.objects.get_or_create(name="Tenants")
        self.user = User.objects.create_user(
            email="user@example.com",
            first_name="User",
            password="pass123"
        )
        self.user.groups.add(Group.objects.get(name="Tenants"))

    def test_popular_search_returns_top_10(self):
        """Тест возврата топ-10 запросов за последние 30 дней."""
        # Создаём 15 запросов (разных)
        for i in range(15):
            SearchQuery.objects.create(user=self.user, query=f"query{i}")

        # Дублируем первые 5, чтобы они стали популярными
        for i in range(5):
            SearchQuery.objects.create(user=self.user, query=f"query{i}")

        url = reverse("popular-search")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 10)  # только топ-10

        # Проверяем сортировку по популярности
        counts = [item["count"] for item in response.data]
        self.assertEqual(counts, sorted(counts, reverse=True))

    def test_popular_search_filters_short_queries(self):
        """Тест фильтрации запросов короче 3 символов."""
        SearchQuery.objects.create(user=self.user, query="ab")  # 2 символа — не попадёт
        SearchQuery.objects.create(user=self.user, query="abc")  # 3 символа — попадёт

        url = reverse("popular-search")
        response = self.client.get(url)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["query"], "abc")

    def test_popular_search_excludes_old_queries(self):
        """Тест исключения запросов старше 30 дней."""
        old_date = timezone.now() - timedelta(days=31)
        old_query = SearchQuery.objects.create(user=self.user, query="old_query")
        # Перезаписываем created_at после сохранения
        SearchQuery.objects.filter(id=old_query.id).update(created_at=old_date)

        new_query = SearchQuery.objects.create(user=self.user, query="new_query")

        url = reverse("popular-search")
        response = self.client.get(url)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["query"], "new_query")

    def test_popular_search_excludes_deleted(self):
        """Тест исключения мягко удалённых запросов."""
        query = SearchQuery.objects.create(user=self.user, query="deleted_query")
        query.is_deleted = True
        query.save()

        url = reverse("popular-search")
        response = self.client.get(url)
        self.assertEqual(len(response.data), 0)

# запуск python manage.py test apps.history