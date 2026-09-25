from django.urls import path
from . import views

urlpatterns = [
    path("listings/", views.GoodsListingListCreateView.as_view(), name="goods-listings"),
    path("listings/<int:listing_id>/", views.GoodsListingDetailView.as_view(), name="goods-listing-detail"),
    path("listings/<int:listing_id>/status/", views.GoodsListingStatusView.as_view(), name="goods-listing-status"),
    path("listings/<int:listing_id>/interest/", views.GoodsInterestCreateView.as_view(), name="goods-listing-interest"),
    path("listings/<int:listing_id>/reports/", views.GoodsReportCreateView.as_view(), name="goods-listing-report"),
]
