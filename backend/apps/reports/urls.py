from django.urls import path
from .views import ReportListCreateView, ReportModerationView

urlpatterns = [
    path("", ReportListCreateView.as_view(), name="reports-list-create"),
    path("moderation/", ReportModerationView.as_view(), name="reports-moderation"),
]
