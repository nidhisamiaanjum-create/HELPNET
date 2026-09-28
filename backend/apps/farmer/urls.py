from django.urls import path
from .views import (
    MyProduceListView,
    ProduceListingDetailView,
    ProduceListingListCreateView,
)

urlpatterns = [
    path("produce/", ProduceListingListCreateView.as_view(), name="farmer-produce-list-create"),
    path("produce/<uuid:id>/", ProduceListingDetailView.as_view(), name="farmer-produce-detail"),
    path("my-produce/", MyProduceListView.as_view(), name="farmer-my-produce"),
]
