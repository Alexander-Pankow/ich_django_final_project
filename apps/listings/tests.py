from django.test import TestCase
from django.contrib.auth.models import Group
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from .models import Listing
from apps.users.models import User
from apps.history.models import SearchQuery, ViewHistory


class ListingModelTest(TestCase):
    """Tests for the Listing model."""  # Тесты модели объявления

    def setUp(self):
        Group.objects.get_or_create(name="Landlords")
        self.landlord = User.objects.create_user(
            email="landlord@example.com",
            first_name="Landlord",
            password="pass123"
        )
        self.landlord.groups.add(Group.objects.get(name="Landlords"))

    def test_listing_creation(self):
        """Test listing creation with default active state."""  # Тест создания объявления
        listing = Listing.objects.create(
            owner=self.landlord,
            title="Cozy Apartment",
            description="Nice place in Berlin",
            city="Berlin",
            price=1200.00,
            rooms=2,
            housing_type="apartment"
        )
        self.assertEqual(listing.title, "Cozy Apartment")
        self.assertEqual(listing.city, "Berlin")
        self.assertTrue(listing.is_active)
        self.assertFalse(listing.is_deleted)

    def test_invalid_postal_code(self):
        """Test validation fails for German postal code with wrong length."""  # Тест валидации немецкого почтового индекса
        listing = Listing(
            owner=self.landlord,
            title="Test",
            description="Test",
            city="Berlin",
            postal_code="1234",  # must be 5 digits
            price=1000,
            rooms=1,
            housing_type="apartment"
        )
        with self.assertRaises(Exception):
            listing.full_clean()

    def test_valid_postal_code(self):
        """Test validation passes for valid 5-digit German postal code."""  # Тест корректного почтового индекса
        listing = Listing(
            owner=self.landlord,
            title="Test",
            description="Test",
            city="Berlin",
            postal_code="10115",
            price=1000,
            rooms=1,
            housing_type="apartment"
        )
        listing.full_clean()  # should not raise


class ListingListViewTest(APITestCase):
    """Tests for listing list view and creation."""  # Тесты списка объявлений и создания

    def setUp(self):
        Group.objects.get_or_create(name="Landlords")
        Group.objects.get_or_create(name="Tenants")
        self.landlord = User.objects.create_user(
            email="landlord@example.com",
            first_name="Landlord",
            password="pass123"
        )
        self.landlord.groups.add(Group.objects.get(name="Landlords"))
        self.tenant = User.objects.create_user(
            email="tenant@example.com",
            first_name="Tenant",
            password="pass123"
        )
        self.tenant.groups.add(Group.objects.get(name="Tenants"))

        self.listing = Listing.objects.create(
            owner=self.landlord,
            title="Berlin Apartment",
            description="Central location",
            city="Berlin",
            price=1500.00,
            rooms=3,
            housing_type="apartment"
        )

    def test_list_listings_public(self):
        """Test public access to listing list."""  # Тест публичного доступа к списку объявлений
        url = reverse("listing-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_create_listing_landlord(self):
        """Test landlord can create a listing."""  # Тест создания объявления арендодателем
        self.client.force_authenticate(user=self.landlord)
        url = reverse("listing-list")
        data = {
            "title": "New Listing",
            "description": "Great place",
            "city": "Munich",
            "price": 2000,
            "rooms": 2,
            "housing_type": "apartment"
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Listing.objects.count(), 2)
        new_listing = Listing.objects.get(title="New Listing")
        self.assertEqual(new_listing.owner, self.landlord)
        self.assertTrue(new_listing.is_active)

    def test_create_listing_tenant_forbidden(self):
        """Test tenant cannot create a listing."""  # Тест запрета создания объявления арендатором
        self.client.force_authenticate(user=self.tenant)
        url = reverse("listing-list")
        data = {
            "title": "New Listing",
            "description": "Great place",
            "city": "Munich",
            "price": 2000,
            "rooms": 2,
            "housing_type": "apartment"
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_search_and_filter(self):
        """Test search and filtering functionality."""  # Тест поиска и фильтрации
        Listing.objects.create(
            owner=self.landlord,
            title="Hamburg House",
            description="Spacious house",
            city="Hamburg",
            price=3000.00,
            rooms=5,
            housing_type="house"
        )
        url = reverse("listing-list")
        # Search by keyword
        response = self.client.get(url, {"search": "Berlin"})
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["city"], "Berlin")

        # Filter by price and city
        response = self.client.get(url, {"price_min": 2000, "city": "Hamburg"})
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["price"], "3000.00")

    def test_search_saves_history(self):
        """Test that search queries are saved to user history."""  # Тест сохранения поискового запроса в историю
        self.client.force_authenticate(user=self.tenant)
        url = reverse("listing-list")
        self.client.get(url, {"search": "central"})
        self.assertTrue(SearchQuery.objects.filter(query="central", user=self.tenant).exists())


class ListingDetailViewTest(APITestCase):
    """Tests for listing detail view."""  # Тесты детального просмотра объявления

    def setUp(self):
        Group.objects.get_or_create(name="Landlords")
        self.landlord = User.objects.create_user(
            email="landlord@example.com",
            first_name="Landlord",
            password="pass123"
        )
        self.landlord.groups.add(Group.objects.get(name="Landlords"))
        self.tenant = User.objects.create_user(
            email="tenant@example.com",
            first_name="Tenant",
            password="pass123"
        )

        self.listing = Listing.objects.create(
            owner=self.landlord,
            title="Berlin Apartment",
            description="Central location",
            city="Berlin",
            price=1500.00,
            rooms=3,
            housing_type="apartment"
        )

    def test_retrieve_listing_public(self):
        """Test public access to listing detail."""  # Тест публичного доступа к деталям объявления
        url = reverse("listing-detail", args=[self.listing.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "Berlin Apartment")

    def test_update_listing_owner(self):
        """Test owner can update their listing."""  # Тест обновления объявления владельцем
        self.client.force_authenticate(user=self.landlord)
        url = reverse("listing-detail", args=[self.listing.id])
        data = {"title": "Updated Title"}
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.listing.refresh_from_db()
        self.assertEqual(self.listing.title, "Updated Title")

    def test_update_listing_non_owner_forbidden(self):
        """Test non-owner cannot update listing."""  # Тест запрета обновления не владельцем
        self.client.force_authenticate(user=self.tenant)
        url = reverse("listing-detail", args=[self.listing.id])
        data = {"title": "Hacked Title"}
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_listing_owner(self):
        """Test owner can soft-delete their listing."""  # Тест мягкого удаления владельцем
        self.client.force_authenticate(user=self.landlord)
        url = reverse("listing-detail", args=[self.listing.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.listing.refresh_from_db()
        self.assertTrue(self.listing.is_deleted)

    def test_view_saves_history(self):
        """Test that listing views are saved to user history."""  # Тест сохранения просмотра в историю
        self.client.force_authenticate(user=self.tenant)
        url = reverse("listing-detail", args=[self.listing.id])
        self.client.get(url)
        self.assertTrue(ViewHistory.objects.filter(listing=self.listing, user=self.tenant).exists())


class PopularListingsViewTest(APITestCase):
    """Tests for popular listings endpoint."""  # Тесты популярных объявлений

    def setUp(self):
        Group.objects.get_or_create(name="Landlords")
        self.landlord = User.objects.create_user(
            email="landlord@example.com",
            first_name="Landlord",
            password="pass123"
        )
        self.landlord.groups.add(Group.objects.get(name="Landlords"))
        self.tenant = User.objects.create_user(
            email="tenant@example.com",
            first_name="Tenant",
            password="pass123"
        )

        self.listing1 = Listing.objects.create(
            owner=self.landlord,
            title="Popular Listing",
            description="Most viewed",
            city="Berlin",
            price=1000.00,
            rooms=1,
            housing_type="apartment"
        )
        self.listing2 = Listing.objects.create(
            owner=self.landlord,
            title="Less Popular",
            description="Less viewed",
            city="Berlin",
            price=1000.00,
            rooms=1,
            housing_type="apartment"
        )

        # Create view records
        ViewHistory.objects.create(user=self.tenant, listing=self.listing1)
        ViewHistory.objects.create(user=self.tenant, listing=self.listing1)

    def test_popular_listings(self):
        """Test retrieving popular listings sorted by view count."""  # Тест получения популярных объявлений
        url = reverse("popular-listings")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        # Most viewed first
        self.assertEqual(response.data[0]["id"], self.listing1.id)

#запуск python manage.py test apps.listings