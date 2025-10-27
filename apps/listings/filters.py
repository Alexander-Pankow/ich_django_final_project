from django_filters import rest_framework as filters
from django.db.models import Q
from .models import Listing
from .choices import HOUSING_TYPE_CHOICES


class ListingFilter(filters.FilterSet):
    """
    Filters for listings.
    """
    # Фильтры для объявлений

    search = filters.CharFilter(method="filter_search")
    price_min = filters.NumberFilter(field_name="price", lookup_expr="gte")
    price_max = filters.NumberFilter(field_name="price", lookup_expr="lte")
    rooms_min = filters.NumberFilter(field_name="rooms", lookup_expr="gte")
    rooms_max = filters.NumberFilter(field_name="rooms", lookup_expr="lte")
    city = filters.CharFilter(field_name="city", lookup_expr="icontains")
    housing_type = filters.ChoiceFilter(choices=HOUSING_TYPE_CHOICES)

    class Meta:
        model = Listing
        fields = []

    def filter_search(self, queryset, name, value):
        """
        Search by title or description.
        """
        # Поиск по заголовку или описанию
        return queryset.filter(
            Q(title__icontains=value) | Q(description__icontains=value)
        )