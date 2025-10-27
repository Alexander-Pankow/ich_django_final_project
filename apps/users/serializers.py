from django.contrib.auth.models import Group
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import User


class RegisterSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration with role assignment (tenant/landlord).
    """
    # Сериализатор регистрации пользователя с назначением роли (арендатор/арендодатель)

    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password]
    )
    password2 = serializers.CharField(write_only=True, required=True)
    role = serializers.ChoiceField(choices=[
        ('tenant', _('Tenant')),        # Арендатор
        ('landlord', _('Landlord'))     # Арендодатель
    ],
        write_only=True
    )

    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'password', 'password2', 'role')
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': False}
        }

    def validate(self, attrs):
        """
        Validate that both password fields match.
        """
        # Проверяет, что пароли совпадают
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({
                "password2": _("The two password fields didn't match.")  # Пароли не совпадают.
            })
        return attrs

    def create(self, validated_data):
        """
        Create a new user and assign to the appropriate group (Tenants/Landlords).
        """
        # Создаёт нового пользователя и добавляет его в группу (Арендаторы/Арендодатели)
        role = validated_data.pop('role')
        validated_data.pop('password2')
        user = User.objects.create_user(**validated_data)

        group_name = 'Landlords' if role == 'landlord' else 'Tenants'
        group, _ = Group.objects.get_or_create(name=group_name)
        user.groups.add(group)
        return user


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for public user profile data (without sensitive fields).
    """
    # Сериализатор для публичных данных профиля (без чувствительной информации)

    class Meta:
        model = User
        fields = ('id', 'email', 'first_name', 'last_name')