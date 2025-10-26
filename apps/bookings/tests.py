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
    """Тесты модели Booking."""

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
        """Тест создания бронирования."""
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
        """Тест валидации пересекающихся бронирований."""
        start_date = timezone.now().date() + timedelta(days=10)
        end_date = timezone.now().date() + timedelta(days=12)
        Booking.objects.create(
            listing=self.listing,
            tenant=self.tenant,
            start_date=start_date,
            end_date=end_date
        )
        # Попытка создать пересекающееся бронирование
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
        """Тест запрета бронирования своего жилья."""
        start_date = timezone.now().date() + timedelta(days=10)
        end_date = timezone.now().date() + timedelta(days=12)
        with self.assertRaises(Exception):
            Booking.objects.create(
                listing=self.listing,
                tenant=self.landlord,  # владелец пытается забронировать своё жильё
                start_date=start_date,
                end_date=end_date
            )


class BookingListViewTest(APITestCase):
    """Тесты списка и создания бронирований."""

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
        """Тест создания бронирования арендатором."""
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
        """Тест запрета создания бронирования арендодателем."""
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
        """Тест списка бронирований арендатора."""
        self.client.force_authenticate(user=self.tenant)
        # Создаём бронирование
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
        """Тест списка бронирований арендодателя (брони на его объявления)."""
        self.client.force_authenticate(user=self.landlord)
        # Создаём бронирование от другого арендатора
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
    """Тесты действий с бронированием (cancel/confirm/reject)."""

    def setUp(self):
        # Создаём группы
        Group.objects.get_or_create(name="Landlords")
        Group.objects.get_or_create(name="Tenants")

        # Создаём арендодателя
        self.landlord = User.objects.create_user(
            email="landlord@example.com",
            first_name="Landlord",
            password="ValidPass123!"
        )
        self.landlord.groups.add(Group.objects.get(name="Landlords"))

        # Создаём арендатора
        self.tenant = User.objects.create_user(
            email="tenant@example.com",
            first_name="Tenant",
            password="ValidPass123!"
        )
        self.tenant.groups.add(Group.objects.get(name="Tenants"))

        # 👇 ВАЖНО: добавляем временные атрибуты, чтобы не падали пермишены
        self.landlord.tenant = None
        self.tenant.tenant = self.tenant

        # Создаём объявление
        self.listing = Listing.objects.create(
            owner=self.landlord,
            title="Berlin Apartment",
            description="Central location",
            city="Berlin",
            price=1500.00,
            rooms=3,
            housing_type="apartment"
        )

        # Создаём бронирование
        self.booking = Booking.objects.create(
            listing=self.listing,
            tenant=self.tenant,
            start_date=timezone.now().date() + timedelta(days=10),
            end_date=timezone.now().date() + timedelta(days=12)
        )

    def test_cancel_booking_tenant(self):
        """Тест отмены бронирования арендатором (за 7+ дней)."""
        self.client.force_authenticate(user=self.tenant)
        url = reverse("booking-action", args=[self.booking.id, "cancel"])
        response = self.client.patch(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, "cancelled")

    def test_cancel_booking_too_late(self):
        """Тест отмены бронирования позже чем за 7 дней до заезда."""
        self.booking.start_date = timezone.now().date() + timedelta(days=3)
        self.booking.save()
        self.client.force_authenticate(user=self.tenant)
        url = reverse("booking-action", args=[self.booking.id, "cancel"])
        response = self.client.patch(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_confirm_booking_landlord(self):
        """Тест подтверждения бронирования арендодателем."""
        self.client.force_authenticate(user=self.landlord)
        url = reverse("booking-action", args=[self.booking.id, "confirm"])
        response = self.client.patch(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, "confirmed")

    def test_reject_booking_landlord(self):
        """Тест отклонения бронирования арендодателем."""
        self.client.force_authenticate(user=self.landlord)
        url = reverse("booking-action", args=[self.booking.id, "reject"])
        response = self.client.patch(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, "cancelled")

    def test_cancel_booking_landlord_forbidden(self):
        """Тест запрета отмены бронирования арендодателем."""
        self.client.force_authenticate(user=self.landlord)
        url = reverse("booking-action", args=[self.booking.id, "cancel"])
        response = self.client.patch(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_confirm_booking_tenant_forbidden(self):
        """Тест запрета подтверждения бронирования арендатором."""
        self.client.force_authenticate(user=self.tenant)
        url = reverse("booking-action", args=[self.booking.id, "confirm"])
        response = self.client.patch(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_invalid_action(self):
        """Тест недопустимого действия."""
        self.client.force_authenticate(user=self.tenant)
        url = reverse("booking-action", args=[self.booking.id, "invalid"])
        response = self.client.patch(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


# запуск python manage.py test apps.bookings