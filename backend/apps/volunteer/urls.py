from django.urls import path
from . import views

urlpatterns = [
    path("opportunities/", views.OpportunityListCreateView.as_view(), name="volunteer-opportunities"),
    path("my-events/", views.MyVolunteerEventsView.as_view(), name="my-volunteer-events"),
    path("opportunities/<int:event_id>/", views.OpportunityDetailView.as_view(), name="volunteer-opportunity-detail"),
    path("opportunities/<int:event_id>/signup/", views.VolunteerSignupView.as_view(), name="volunteer-signup"),
    path("opportunities/<int:event_id>/attendance/", views.AttendanceView.as_view(), name="volunteer-attendance"),
    path("opportunities/<int:event_id>/messages/", views.EventMessagesView.as_view(), name="volunteer-messages"),
    path("opportunities/<int:event_id>/certificates/", views.CertificateListIssueView.as_view(), name="volunteer-certificates"),
    path("certificates/", views.CertificateListIssueView.as_view(), name="volunteer-certificate-list"),
    path("certificates/<int:certificate_id>/pdf/", views.CertificatePdfView.as_view(), name="volunteer-certificate-pdf"),
    path("profile/", views.VolunteerProfileView.as_view(), name="volunteer-profile"),
    path("search/", views.VolunteerSearchView.as_view(), name="volunteer-search"),
    path("admin/", views.AdminVolunteersView.as_view(), name="admin-volunteers"),
]
