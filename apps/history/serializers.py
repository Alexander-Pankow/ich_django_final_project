from rest_framework import serializers


class PopularSearchSerializer(serializers.Serializer):
    """
    Serializer for popular search query statistics.
    """
    # Сериализатор для статистики популярных поисковых запросов

    query = serializers.CharField(read_only=True)
    count = serializers.IntegerField(read_only=True)