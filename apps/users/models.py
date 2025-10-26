from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _


class CustomUserManager(BaseUserManager):
    """Custom user manager that uses email instead of username."""
    # Менеджер для кастомного пользователя с использованием email вместо username

    use_in_migrations = True

    def create_user(self, email, password=None, **extra_fields):
        """Create and return a regular user with an email and password."""
        # Создаёт и возвращает обычного пользователя с email и паролем
        if not email:
            raise ValueError(_("The Email field must be set"))  # Поле Email должно быть заполнено
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """Create and return a superuser with staff and admin privileges."""
        # Создаёт и возвращает суперпользователя с правами администратора
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError(_("Superuser must have is_staff=True."))  # Суперпользователь должен иметь is_staff=True
        if extra_fields.get("is_superuser") is not True:
            raise ValueError(_("Superuser must have is_superuser=True."))  # Суперпользователь должен иметь is_superuser=True

        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    """Custom User model with email as the unique identifier."""
    # Кастомная модель пользователя с email в качестве уникального идентификатора

    username = None  # Убираем username
    email = models.EmailField(
        _('Email address'),  # Адрес электронной почты
        unique=True
    )
    first_name = models.CharField(
        _('First name'),  # Имя
        max_length=50,
        blank=False
    )
    last_name = models.CharField(
        _('Last name'),  # Фамилия
        max_length=50,
        blank=True
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name']

    objects = CustomUserManager()

    class Meta:
        verbose_name = _('User')  # Пользователь
        verbose_name_plural = _('Users')  # Пользователи

    def __str__(self):
        return self.email