from django.urls import path
from .views import (
    MyProduceListView,
    ProduceListingDetailView,
    ProduceListingListCreateView,
    ProducePriceRangeView,
    ProduceListingReportView,
)

urlpatterns = [
    path("produce/", ProduceListingListCreateView.as_view(), name="farmer-produce-list-create"),
    path("produce/<uuid:id>/price-range/", ProducePriceRangeView.as_view(), name="farmer-produce-price-range"),
    path("produce/<uuid:id>/reports/", ProduceListingReportView.as_view(), name="farmer-produce-report"),
    path("produce/<uuid:id>/", ProduceListingDetailView.as_view(), name="farmer-produce-detail"),
    path("my-produce/", MyProduceListView.as_view(), name="farmer-my-produce"),
]
