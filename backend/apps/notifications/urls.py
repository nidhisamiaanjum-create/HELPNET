from django.urls import path

from . import views


urlpatterns = [
    path("", views.NotificationListView.as_view(), name="notification-list"),
    path("<uuid:notification_id>/read/", views.NotificationReadView.as_view(), name="notification-read"),
]