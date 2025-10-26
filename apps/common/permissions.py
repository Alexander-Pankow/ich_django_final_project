from django.utils.translation import gettext_lazy as _
from rest_framework import permissions


class IsLandlord(permissions.BasePermission):
    """Allow access only to landlords."""
    # Разрешает доступ только арендодателям

    message = _("Access allowed for landlords only.")  # Доступ разрешён только арендодателям.

    def has_permission(self, request, view):
        """Check if user is authenticated and belongs to the 'Landlords' group."""
        # Проверяет, авторизован ли пользователь и состоит ли в группе арендодателей
        return (
            request.user.is_authenticated
            and request.user.groups.filter(name="Landlords").exists()
        )


class IsTenant(permissions.BasePermission):
    """Allow access only to tenants."""
    # Разрешает доступ только арендаторам

    message = _("Access allowed for tenants only.")  # Доступ разрешён только арендаторам.

    def has_permission(self, request, view):
        """Check if user is authenticated and belongs to the 'Tenants' group."""
        # Проверяет, авторизован ли пользователь и состоит ли в группе арендаторов
        return (
            request.user.is_authenticated
            and request.user.groups.filter(name="Tenants").exists()
        )


class IsOwner(permissions.BasePermission):
    """Allow access only to the owner of the object."""
    # Разрешает доступ только владельцу объекта

    message = _("You are not the owner of this object.")  # Вы не являетесь владельцем этого объекта.

    def has_object_permission(self, request, view, obj):
        """Check if the requesting user is the owner of the object."""
        # Проверяет, является ли пользователь владельцем объекта
        if not request.user.is_authenticated:
            return False
        return obj.owner == request.user


class IsBookingOwnerOrLandlord(permissions.BasePermission):
    """Allow access to the booking tenant or the listing landlord."""
    # Разрешает доступ арендатору бронирования или арендодателю объявления

    message = _("You do not have permission to access this booking.")  # У вас нет прав для доступа к этому бронированию.

    def has_object_permission(self, request, view, obj):
        """Check if user is either the booking tenant or the listing owner."""
        # Проверяет, является ли пользователь арендатором бронирования или владельцем объявления
        if not request.user.is_authenticated:
            return False
        return (
            obj.tenant == request.user
            or obj.listing.owner == request.user
        )