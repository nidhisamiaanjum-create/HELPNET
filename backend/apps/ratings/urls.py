from django.urls import path
from .views import RatingListCreateView, UserRatingSummaryView

urlpatterns = [
    path("", RatingListCreateView.as_view(), name="ratings-list-create"),
    path("summary/<uuid:user_id>/", UserRatingSummaryView.as_view(), name="user-rating-summary"),
]
