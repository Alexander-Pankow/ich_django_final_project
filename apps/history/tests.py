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
    """
    Tests for history models (SearchQuery and ViewHistory).
    """
    # Тесты моделей истории (поисковые запросы и просмотры)

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
        """
        Test creating a search query.
        """
        # Тест создания поискового запроса
        query = SearchQuery.objects.create(user=self.user, query="central")
        self.assertEqual(query.query, "central")
        self.assertEqual(query.user, self.user)

    def test_view_history_creation(self):
        """
        Test creating a view history record.
        """
        # Тест создания записи истории просмотра
        view = ViewHistory.objects.create(user=self.user, listing=self.listing)
        self.assertEqual(view.user, self.user)
        self.assertEqual(view.listing, self.listing)


class PopularSearchViewTest(APITestCase):
    """
    Tests for popular search queries endpoint.
    """
    # Тесты популярных поисковых запросов

    def setUp(self):
        Group.objects.get_or_create(name="Tenants")
        self.user = User.objects.create_user(
            email="user@example.com",
            first_name="User",
            password="pass123"
        )
        self.user.groups.add(Group.objects.get(name="Tenants"))

    def test_popular_search_returns_top_10(self):
        """
        Test that the endpoint returns top 10 queries from the last 30 days.
        """
        # Тест возврата топ-10 запросов за последние 30 дней
        for i in range(15):
            SearchQuery.objects.create(user=self.user, query=f"query{i}")

        for i in range(5):
            SearchQuery.objects.create(user=self.user, query=f"query{i}")

        url = reverse("popular-search")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 10)  # Only top 10

        counts = [item["count"] for item in response.data]
        self.assertEqual(counts, sorted(counts, reverse=True))

    def test_popular_search_filters_short_queries(self):
        """
        Test that queries shorter than 3 characters are excluded.
        """
        # Тест фильтрации запросов короче 3 символов
        SearchQuery.objects.create(user=self.user, query="ab")   # 2 chars — excluded
        SearchQuery.objects.create(user=self.user, query="abc")  # 3 chars — included

        url = reverse("popular-search")
        response = self.client.get(url)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["query"], "abc")

    def test_popular_search_excludes_old_queries(self):
        """
        Test that queries older than 30 days are excluded.
        """
        # Тест исключения запросов старше 30 дней
        old_date = timezone.now() - timedelta(days=31)
        old_query = SearchQuery.objects.create(user=self.user, query="old_query")
        SearchQuery.objects.filter(id=old_query.id).update(created_at=old_date)

        SearchQuery.objects.create(user=self.user, query="new_query")

        url = reverse("popular-search")
        response = self.client.get(url)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["query"], "new_query")

    def test_popular_search_excludes_deleted(self):
        """
        Test that soft-deleted queries are excluded.
        """
        # Тест исключения мягко удалённых запросов
        query = SearchQuery.objects.create(user=self.user, query="deleted_query")
        query.is_deleted = True
        query.save()

        url = reverse("popular-search")
        response = self.client.get(url)
        self.assertEqual(len(response.data), 0)

# запуск python manage.py test apps.history