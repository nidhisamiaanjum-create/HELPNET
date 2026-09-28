from django.urls import path

from . import views


urlpatterns = [
    path("donor-profile/", views.DonorProfileView.as_view(), name="donor-profile"),
    path("donors/", views.DonorSearchView.as_view(), name="donor-search"),
    path("requests/", views.BloodRequestListCreateView.as_view(), name="blood-request-list-create"),
    path("requests/<uuid:request_id>/matches/", views.BloodRequestMatchesView.as_view(), name="blood-request-matches"),
    path("requests/<uuid:request_id>/complete/", views.BloodRequestCompleteView.as_view(), name="blood-request-complete"),
    path("requests/<uuid:request_id>/close/", views.BloodRequestCloseView.as_view(), name="blood-request-close"),
    path("donations/", views.DonationHistoryView.as_view(), name="donation-history"),
]