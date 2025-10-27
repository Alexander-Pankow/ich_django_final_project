from django.test import TestCase
from django.contrib.auth.models import Group
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from .models import User


class UserModelTest(TestCase):
    """
    Tests for the custom User model.
    """
    # Тесты модели пользователя

    def test_user_creation(self):
        """
        Test regular user creation.
        """
        # Тест создания обычного пользователя
        user = User.objects.create_user(
            email="test@example.com",
            first_name="Test",
            password="securepassword123"
        )
        self.assertEqual(user.email, "test@example.com")
        self.assertEqual(user.first_name, "Test")
        self.assertTrue(user.check_password("securepassword123"))
        self.assertFalse(user.is_staff)
        self.assertTrue(user.is_active)

    def test_superuser_creation(self):
        """
        Test superuser creation.
        """
        # Тест создания суперпользователя
        superuser = User.objects.create_superuser(
            email="admin@example.com",
            first_name="Admin",
            password="securepassword123"
        )
        self.assertTrue(superuser.is_staff)
        self.assertTrue(superuser.is_superuser)


class RegisterViewTest(APITestCase):
    """
    Tests for user registration endpoint.
    """
    # Тесты регистрации пользователя

    def setUp(self):
        Group.objects.get_or_create(name="Landlords")
        Group.objects.get_or_create(name="Tenants")

    def test_register_tenant(self):
        """
        Test tenant registration.
        """
        # Тест регистрации арендатора
        url = reverse("register")
        data = {
            "email": "tenant@example.com",
            "first_name": "Anna",
            "password": "secure123!",
            "password2": "secure123!",
            "role": "tenant"
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(email="tenant@example.com").exists())
        user = User.objects.get(email="tenant@example.com")
        self.assertTrue(user.groups.filter(name="Tenants").exists())

    def test_register_landlord(self):
        """
        Test landlord registration.
        """
        # Тест регистрации арендодателя
        url = reverse("register")
        data = {
            "email": "landlord@example.com",
            "first_name": "Max",
            "password": "secure123!",
            "password2": "secure123!",
            "role": "landlord"
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(email="landlord@example.com")
        self.assertTrue(user.groups.filter(name="Landlords").exists())

    def test_password_mismatch(self):
        """
        Test registration fails when passwords do not match.
        """  # Тест несовпадения паролей
        url = reverse("register")
        data = {
            "email": "user@example.com",
            "first_name": "User",
            "password": "ValidPass123!",
            "password2": "Mismatch123!",
            "role": "tenant"
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password2", response.data)

    def test_duplicate_email(self):
        """
        Test registration fails with duplicate email.
        """
        # Тест дублирования email
        User.objects.create_user(email="user@example.com", first_name="User", password="pass123")
        url = reverse("register")
        data = {
            "email": "user@example.com",
            "first_name": "New",
            "password": "pass123",
            "password2": "pass123",
            "role": "tenant"
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class CurrentUserViewTest(APITestCase):
    """
    Tests for current user detail endpoint.
    """
    # Тесты получения текущего пользователя

    def setUp(self):
        self.user = User.objects.create_user(
            email="current@example.com",
            first_name="Current",
            password="pass123"
        )

    def test_get_current_user(self):
        """
        Test authenticated user can retrieve their own data.
        """
        # Тест получения данных текущего пользователя
        self.client.force_authenticate(user=self.user)
        url = reverse("current-user")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], "current@example.com")
        self.assertEqual(response.data["first_name"], "Current")

    def test_unauthenticated_access(self):
        """
        Test unauthenticated access is denied.
        """
        # Тест доступа без аутентификации
        url = reverse("current-user")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

#запуск python manage.py test apps.users  все сразу python manage.py test