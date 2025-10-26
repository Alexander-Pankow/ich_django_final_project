from datetime import timedelta
from django.test import TestCase
from django.contrib.auth.models import Group
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework import status
from .models import Booking
from apps.users.models import User
from apps.listings.models import Listing


class BookingModelTest(TestCase):
    """Booking model tests."""  # Тесты модели бронирования

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

    def test_booking_creation(self):
        """Test booking creation."""  # Тест создания бронирования
        start_date = timezone.now().date() + timedelta(days=10)
        end_date = timezone.now().date() + timedelta(days=12)
        booking = Booking.objects.create(
            listing=self.listing,
            tenant=self.tenant,
            start_date=start_date,
            end_date=end_date
        )
        self.assertEqual(booking.total_price, 3000.00)
        self.assertEqual(booking.status, "pending")

    def test_overlapping_booking_validation(self):
        """Test overlapping booking validation."""  # Тест валидации пересекающихся бронирований
        start_date = timezone.now().date() + timedelta(days=10)
        end_date = timezone.now().date() + timedelta(days=12)
        Booking.objects.create(
            listing=self.listing,
            tenant=self.tenant,
            start_date=start_date,
            end_date=end_date
        )
        overlapping_start = timezone.now().date() + timedelta(days=11)
        overlapping_end = timezone.now().date() + timedelta(days=13)
        with self.assertRaises(Exception):
            Booking.objects.create(
                listing=self.listing,
                tenant=self.tenant,
                start_date=overlapping_start,
                end_date=overlapping_end
            )

    def test_cannot_book_own_listing(self):
        """Test that a user cannot book their own listing."""  # Тест запрета бронирования своего жилья
        start_date = timezone.now().date() + timedelta(days=10)
        end_date = timezone.now().date() + timedelta(days=12)
        with self.assertRaises(Exception):
            Booking.objects.create(
                listing=self.listing,
                tenant=self.landlord,
                start_date=start_date,
                end_date=end_date
            )


class BookingListViewTest(APITestCase):
    """Tests for listing and creating bookings."""  # Тесты списка и создания бронирований

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

    def test_create_booking_tenant(self):
        """Test tenant can create a booking."""  # Тест создания бронирования арендатором
        self.client.force_authenticate(user=self.tenant)
        url = reverse("booking-list")
        start_date = (timezone.now().date() + timedelta(days=10)).isoformat()
        end_date = (timezone.now().date() + timedelta(days=12)).isoformat()
        data = {
            "listing": self.listing.id,
            "start_date": start_date,
            "end_date": end_date
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Booking.objects.count(), 1)
        booking = Booking.objects.first()
        self.assertEqual(booking.tenant, self.tenant)
        self.assertEqual(booking.total_price, 3000.00)

    def test_create_booking_landlord_forbidden(self):
        """Test landlord cannot create a booking."""  # Тест запрета создания бронирования арендодателем
        self.client.force_authenticate(user=self.landlord)
        url = reverse("booking-list")
        start_date = (timezone.now().date() + timedelta(days=10)).isoformat()
        end_date = (timezone.now().date() + timedelta(days=12)).isoformat()
        data = {
            "listing": self.listing.id,
            "start_date": start_date,
            "end_date": end_date
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_bookings_tenant(self):
        """Test tenant can list their bookings."""  # Тест списка бронирований арендатора
        self.client.force_authenticate(user=self.tenant)
        start_date = timezone.now().date() + timedelta(days=10)
        end_date = timezone.now().date() + timedelta(days=12)
        Booking.objects.create(
            listing=self.listing,
            tenant=self.tenant,
            start_date=start_date,
            end_date=end_date
        )
        url = reverse("booking-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_list_bookings_landlord(self):
        """Test landlord can list bookings for their listings."""  # Тест списка бронирований арендодателя
        self.client.force_authenticate(user=self.landlord)
        other_tenant = User.objects.create_user(
            email="other@example.com",
            first_name="Other",
            password="pass123"
        )
        other_tenant.groups.add(Group.objects.get(name="Tenants"))
        start_date = timezone.now().date() + timedelta(days=10)
        end_date = timezone.now().date() + timedelta(days=12)
        Booking.objects.create(
            listing=self.listing,
            tenant=other_tenant,
            start_date=start_date,
            end_date=end_date
        )
        url = reverse("booking-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)


class BookingActionViewTest(APITestCase):
    """Tests for booking actions (cancel/confirm/reject)."""  # Тесты действий с бронированием

    def setUp(self):
        Group.objects.get_or_create(name="Landlords")
        Group.objects.get_or_create(name="Tenants")

        self.landlord = User.objects.create_user(
            email="landlord@example.com",
            first_name="Landlord",
            password="ValidPass123!"
        )
        self.landlord.groups.add(Group.objects.get(name="Landlords"))

        self.tenant = User.objects.create_user(
            email="tenant@example.com",
            first_name="Tenant",
            password="ValidPass123!"
        )
        self.tenant.groups.add(Group.objects.get(name="Tenants"))

        # Temporary workaround for permission logic
        self.landlord.tenant = None
        self.tenant.tenant = self.tenant

        self.listing = Listing.objects.create(
            owner=self.landlord,
            title="Berlin Apartment",
            description="Central location",
            city="Berlin",
            price=1500.00,
            rooms=3,
            housing_type="apartment"
        )

        self.booking = Booking.objects.create(
            listing=self.listing,
            tenant=self.tenant,
            start_date=timezone.now().date() + timedelta(days=10),
            end_date=timezone.now().date() + timedelta(days=12)
        )

    def test_cancel_booking_tenant(self):
        """Test tenant can cancel booking (≥7 days before start)."""  # Отмена брони арендатором (за 7+ дней)
        self.client.force_authenticate(user=self.tenant)
        url = reverse("booking-action", args=[self.booking.id, "cancel"])
        response = self.client.patch(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, "cancelled")

    def test_cancel_booking_too_late(self):
        """Test tenant cannot cancel booking <7 days before start."""  # Отмена позже чем за 7 дней запрещена
        self.booking.start_date = timezone.now().date() + timedelta(days=3)
        self.booking.save()
        self.client.force_authenticate(user=self.tenant)
        url = reverse("booking-action", args=[self.booking.id, "cancel"])
        response = self.client.patch(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_confirm_booking_landlord(self):
        """Test landlord can confirm a booking."""  # Подтверждение брони арендодателем
        self.client.force_authenticate(user=self.landlord)
        url = reverse("booking-action", args=[self.booking.id, "confirm"])
        response = self.client.patch(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, "confirmed")

    def test_reject_booking_landlord(self):
        """Test landlord can reject a booking."""  # Отклонение брони арендодателем
        self.client.force_authenticate(user=self.landlord)
        url = reverse("booking-action", args=[self.booking.id, "reject"])
        response = self.client.patch(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, "cancelled")

    def test_cancel_booking_landlord_forbidden(self):
        """Test landlord cannot cancel a booking."""  # Арендодатель не может отменять бронь
        self.client.force_authenticate(user=self.landlord)
        url = reverse("booking-action", args=[self.booking.id, "cancel"])
        response = self.client.patch(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_confirm_booking_tenant_forbidden(self):
        """Test tenant cannot confirm a booking."""  # Арендатор не может подтверждать бронь
        self.client.force_authenticate(user=self.tenant)
        url = reverse("booking-action", args=[self.booking.id, "confirm"])
        response = self.client.patch(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_invalid_action(self):
        """Test invalid action returns 400."""  # Недопустимое действие возвращает 400
        self.client.force_authenticate(user=self.tenant)
        url = reverse("booking-action", args=[self.booking.id, "invalid"])
        response = self.client.patch(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


# запуск python manage.py test apps.bookings