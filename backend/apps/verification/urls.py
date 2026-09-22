from django.urls import path
from . import views


urlpatterns = [
    path("", views.nid_verification_page, name="nid-verification"),
]
