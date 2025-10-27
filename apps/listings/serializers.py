from rest_framework import serializers
from .models import Listing
from .choices import HOUSING_TYPE_CHOICES


class ListingSerializer(serializers.ModelSerializer):
    """
    Serializer for creating, updating, and viewing housing listings.
    """
    # Сериализатор для создания, обновления и просмотра объявлений о жилье

    owner = serializers.StringRelatedField(read_only=True)
    housing_type = serializers.ChoiceField(choices=HOUSING_TYPE_CHOICES)

    class Meta:
        model = Listing
        fields = (
            'id', 'title', 'description', 'street', 'city', 'postal_code',
            'price', 'rooms', 'housing_type', 'is_active',
            'created_at', 'updated_at', 'owner'
        )
        read_only_fields = ('owner', 'is_active', 'created_at', 'updated_at')

    def create(self, validated_data):
        """
        Create a new listing with the current user as owner and active status.
        """
        # Создаёт новое объявление с текущим пользователем как владельцем и статусом «активно»
        validated_data['owner'] = self.context['request'].user
        validated_data['is_active'] = True
        return super().create(validated_data)

    def update(self, instance, validated_data):
        """
        Update listing while protecting owner and is_active fields from modification.
        """
        # Обновляет объявление, защищая поля owner и is_active от изменения
        validated_data.pop('owner', None)
        validated_data.pop('is_active', None)
        return super().update(instance, validated_data)