from django.urls import path

from .views import (
    RegisterView,
    LoginView,
    ProtectedView,
    AdminOnlyView,
)


urlpatterns = [

    path(
        "register/",
        RegisterView.as_view(),
        name="register"
    ),

    path(
        "login/",
        LoginView.as_view(),
        name="login"
    ),

    # S2-T06: No Token Test
    path(
        "protected/",
        ProtectedView.as_view(),
        name="protected"
    ),

    # S2-T06: Wrong Role Test
    path(
        "admin-only/",
        AdminOnlyView.as_view(),
        name="admin-only"
    ),

]