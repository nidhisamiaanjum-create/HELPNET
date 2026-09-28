from django.urls import path
from .views import (
    AvailableCollectorsView,
    CollectorProfileView,
    WastePickupRequestDetailView,
    WastePickupRequestListCreateView,
)

urlpatterns = [
    path("requests/", WastePickupRequestListCreateView.as_view(), name="waste-requests-list-create"),
    path("requests/<uuid:id>/", WastePickupRequestDetailView.as_view(), name="waste-request-detail"),
    path("collectors/", AvailableCollectorsView.as_view(), name="waste-available-collectors"),
    path("collectors/<uuid:user_id>/", CollectorProfileView.as_view(), name="waste-collector-profile"),
]
