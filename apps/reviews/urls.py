from django.urls import path

from .views import ReviewListView


# URL pattern for listing reviews and creating a new review
# Эндпоинт для получения и создания отзывов к объявлению
urlpatterns = [
    path(
        "listings/<int:listing_id>/reviews/",
        ReviewListView.as_view(),
        name="review-list"
    ),
]