from django.urls import path

from . import views

urlpatterns = [
    path("questions/", views.HealthQuestionListCreateView.as_view(), name="health-questions"),
    path("questions/<int:question_id>/", views.HealthQuestionDetailView.as_view(), name="health-question-detail"),
    path("questions/<int:question_id>/replies/", views.HealthReplyListCreateView.as_view(), name="health-question-replies"),
    path("professionals/", views.HealthProfessionalListView.as_view(), name="health-professionals"),
    path("professionals/<int:professional_id>/verification/", views.HealthProfessionalVerificationView.as_view(), name="health-professional-verification"),
]
