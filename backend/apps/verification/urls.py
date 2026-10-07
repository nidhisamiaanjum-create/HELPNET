from django.urls import path

from . import views


urlpatterns = [
    path(
        "",
        views.nid_verification_page,
        name="nid-verification",
    ),
    path(
        "submit/",
        views.VerificationSubmitView.as_view(),
        name="verification-submit",
    ),
    path(
        "status/",
        views.VerificationStatusView.as_view(),
        name="verification-status",
    ),
    path(
        "admin/",
        views.AdminVerificationListView.as_view(),
        name="admin-verification-list",
    ),
    path(
    "admin/<uuid:verification_id>/action/",
    views.AdminVerificationActionView.as_view(),
    name="admin-verification-action",
    ),
    path(
    "admin/logs/",
    views.AdminActionLogListView.as_view(),
    name="admin-action-logs",
),
]