from django.urls import path

from .views import (
    RegisterView,
    LoginView,
    LogoutView,
    MeView,
    PasswordResetRequestView,
    PasswordResetConfirmView,
    UserProfilesView, UserProfileDetailView, ActiveProfileView,
    NGOApprovalView,    PendingNGOApprovalListView,
)


urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path(
        "password-reset/",
        PasswordResetRequestView.as_view(),
        name="password-reset"
    ),
    path(
        "password-reset-confirm/",
        PasswordResetConfirmView.as_view(),
        name="password-reset-confirm"
    ),
     path("me/", MeView.as_view(), name="me"),
    path("profiles/", UserProfilesView.as_view(), name="profiles"),
    path("profiles/<int:id>/", UserProfileDetailView.as_view(), name="profile-detail"),
    path("active-profile/", ActiveProfileView.as_view(), name="active-profile"),
    path(
        "ngo-profiles/<int:profile_id>/approval/",
        NGOApprovalView.as_view(),
        name="ngo-profile-approval",
    ),
    path(
        "ngo-profiles/pending/",
        PendingNGOApprovalListView.as_view(),
        name="pending-ngo-approvals",
    ),
]
