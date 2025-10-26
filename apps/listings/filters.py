from django_filters import rest_framework as filters
from django.db.models import Q
from .models import Listing
from .choices import HOUSING_TYPE_CHOICES


class ListingFilter(filters.FilterSet):
    """Фильтры для объявлений."""
    # Поиск по заголовку или описанию
    search = filters.CharFilter(method="filter_search")
    # Фильтрация по цене
    price_min = filters.NumberFilter(field_name="price", lookup_expr="gte")
    price_max = filters.NumberFilter(field_name="price", lookup_expr="lte")
    # Фильтрация по комнатам
    rooms_min = filters.NumberFilter(field_name="rooms", lookup_expr="gte")
    rooms_max = filters.NumberFilter(field_name="rooms", lookup_expr="lte")
    # Город (нечувствительно к регистру)
    city = filters.CharFilter(field_name="city", lookup_expr="icontains")
    # Тип жилья (точное совпадение)
    housing_type = filters.ChoiceFilter(choices=HOUSING_TYPE_CHOICES)

    class Meta:
        model = Listing
        fields = []  # Все поля заданы вручную

    def filter_search(self, queryset, name, value):
        """Поиск по заголовку или описанию."""
        return queryset.filter(
            Q(title__icontains=value) | Q(description__icontains=value)
        )