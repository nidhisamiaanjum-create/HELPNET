from django.urls import path

from .views import (
    CollectorProfileView,
    AvailableVolunteerCollectorsView,
    WasteCollectorListCreateView,
    WasteCollectorRatingListCreateView,
    WastePickupRequestDetailView,
    WastePickupRequestListCreateView,
)


urlpatterns = [
    path(
        "requests/",
        WastePickupRequestListCreateView.as_view(),
        name="waste-requests-list-create",
    ),

    path(
        "requests/<uuid:id>/",
        WastePickupRequestDetailView.as_view(),
        name="waste-request-detail",
    ),

    path(
        "collectors/available/",
        AvailableVolunteerCollectorsView.as_view(),
        name="waste-available-collectors",
    ),

    path(
        "collectors/",
        WasteCollectorListCreateView.as_view(),
        name="waste-collectors",
    ),

    path(
        "collectors/<uuid:collector_id>/",
        CollectorProfileView.as_view(),
        name="waste-collector-profile",
    ),

    path(
        "collectors/<uuid:collector_id>/ratings/",
        WasteCollectorRatingListCreateView.as_view(),
        name="waste-collector-ratings",
    ),
]
