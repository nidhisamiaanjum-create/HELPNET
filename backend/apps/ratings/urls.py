from django.urls import path
from . import views

urlpatterns = [
    path("", views.RatingCreateView.as_view(), name="ratings-list-create"),
    path("create/", views.RatingCreateView.as_view(), name="rating-create"),
    path("summary/<uuid:user_id>/", views.UserRatingSummaryView.as_view(), name="user-rating-summary"),
    path("users/<uuid:user_id>/", views.UserRatingsView.as_view(), name="user-ratings"),
    path("users/<uuid:user_id>/average/", views.UserRatingAverageView.as_view(), name="user-rating-average"),
    path("<uuid:user_id>/", views.UserRatingsView.as_view(), name="user-ratings-short"),
    path("<uuid:user_id>/average/", views.UserRatingAverageView.as_view(), name="user-rating-average-short"),
]
