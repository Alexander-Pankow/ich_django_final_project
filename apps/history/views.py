from datetime import timedelta
from typing import Any
from django.db.models import Count
from django.db.models.functions import Length
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from .models import SearchQuery
from .serializers import PopularSearchSerializer


@extend_schema_view(
    get=extend_schema(
        summary=_("Popular search queries"),  # Популярные поисковые запросы
        description=_(
            "Returns top 10 search queries from the last 30 days. "
            "Only non-empty queries with length > 2 characters are included."
        ),
        responses={200: PopularSearchSerializer(many=True)},
    ),
)
class PopularSearchView(generics.GenericAPIView):
    """
    Return top 10 popular search queries.
    """
    # Возвращает топ-10 популярных поисковых запросов

    serializer_class = PopularSearchSerializer
    permission_classes = [AllowAny]
    def get(self, request, *args: Any, **kwargs: Any) -> Response:
        """
        Handle GET request for popular search queries.
        """
        # Обрабатывает GET-запрос для популярных запросов
        since = timezone.now() - timedelta(days=30)

        queryset = (
            SearchQuery.objects.filter(
                is_deleted=False,
                created_at__gte=since,
                query__isnull=False,
            )
            .annotate(query_length=Length('query'))  # добавляем длину запроса
            .filter(query_length__gt=2)              # фильтруем только > 2 символов
            .exclude(query="")                       # исключаем пустые строки
            .values("query")                         # группируем по тексту запроса
            .annotate(count=Count("query"))          # считаем количество
            .order_by("-count")[:10]                 # топ-10
        )

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)