from datetime import timedelta
from django.test import TestCase
from django.contrib.auth.models import Group
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework import status
from .models import Review
from apps.users.models import User
from apps.listings.models import Listing
from apps.bookings.models import Booking


class ReviewModelTest(TestCase):
    """Tests for the Review model."""  # Тесты модели отзыва

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
        # Create a booking with future dates to pass initial validation
        self.booking = Booking.objects.create(
            listing=self.listing,
            tenant=self.tenant,
            start_date=timezone.now().date() + timedelta(days=1),
            end_date=timezone.now().date() + timedelta(days=5),
            status="completed"
        )
        # Update dates to past for review eligibility
        Booking.objects.filter(id=self.booking.id).update(
            start_date=timezone.now().date() - timedelta(days=10),
            end_date=timezone.now().date() - timedelta(days=5)
        )
        self.booking.refresh_from_db()

    def test_review_creation(self):
        """Test creating a review."""  # Тест создания отзыва
        review = Review.objects.create(
            booking=self.booking,
            rating=5,
            comment="Great place!"
        )
        self.assertEqual(review.rating, 5)
        self.assertEqual(review.comment, "Great place!")
        self.assertEqual(review.listing, self.listing)
        self.assertEqual(review.author, self.tenant)

    def test_one_review_per_booking(self):
        """Test that only one review per booking is allowed."""  # Тест ограничения: один отзыв на бронирование
        Review.objects.create(
            booking=self.booking,
            rating=4,
            comment="Nice"
        )
        with self.assertRaises(Exception):
            Review.objects.create(
                booking=self.booking,
                rating=5,
                comment="Another"
            )


class ReviewListViewTest(APITestCase):
    """Tests for listing and creating reviews."""  # Тесты списка и создания отзывов

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
        # Completed booking with future dates (to pass validation)
        self.booking = Booking.objects.create(
            listing=self.listing,
            tenant=self.tenant,
            start_date=timezone.now().date() + timedelta(days=1),
            end_date=timezone.now().date() + timedelta(days=5),
            status="completed"
        )
        # Adjust to past dates for review eligibility
        Booking.objects.filter(id=self.booking.id).update(
            start_date=timezone.now().date() - timedelta(days=10),
            end_date=timezone.now().date() - timedelta(days=5)
        )
        self.booking.refresh_from_db()

    def test_create_review(self):
        """Test tenant can create a review after stay completion."""  # Тест создания отзыва арендатором после проживания
        self.client.force_authenticate(user=self.tenant)
        url = reverse("review-list", kwargs={"listing_id": self.listing.id})
        data = {
            "booking": self.booking.id,
            "rating": 5,
            "comment": "Excellent!"
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Review.objects.filter(booking=self.booking).exists())

    def test_create_review_without_completed_booking(self):
        """Test review creation is blocked without a completed booking."""  # Тест запрета без завершённого бронирования
        future_booking = Booking.objects.create(
            listing=self.listing,
            tenant=self.tenant,
            start_date=timezone.now().date() + timedelta(days=10),
            end_date=timezone.now().date() + timedelta(days=12),
            status="pending"
        )
        self.client.force_authenticate(user=self.tenant)
        url = reverse("review-list", kwargs={"listing_id": self.listing.id})
        data = {
            "booking": future_booking.id,
            "rating": 5,
            "comment": "Not allowed!"
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_review_by_landlord_forbidden(self):
        """Test landlord cannot create a review."""  # Тест запрета для арендодателя
        self.client.force_authenticate(user=self.landlord)
        url = reverse("review-list", kwargs={"listing_id": self.listing.id})
        data = {
            "booking": self.booking.id,
            "rating": 5,
            "comment": "I can't review my own listing!"
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_reviews_public(self):
        """Test public access to reviews list."""  # Тест публичного доступа к отзывам
        Review.objects.create(
            booking=self.booking,
            rating=5,
            comment="Great!"
        )
        url = reverse("review-list", kwargs={"listing_id": self.listing.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_create_review_unauthenticated_forbidden(self):
        """Test unauthenticated users cannot create reviews."""  # Тест запрета для неавторизованных
        url = reverse("review-list", kwargs={"listing_id": self.listing.id})
        data = {
            "booking": self.booking.id,
            "rating": 5,
            "comment": "Anonymous review"
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

#запуск python manage.py test apps.reviews