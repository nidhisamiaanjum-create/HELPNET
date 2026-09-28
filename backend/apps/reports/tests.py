from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from .models import Report

User = get_user_model()


class ReportTests(APITestCase):
    def setUp(self):
        self.citizen = User.objects.create_user(
            phone_number="01711117777",
            email="citizen_rep@example.com",
            full_name="Citizen Reporter",
            password="password123",
            role="Citizen",
        )
        self.reported = User.objects.create_user(
            phone_number="01822228888",
            email="reported_col@example.com",
            full_name="Reported User",
            password="password123",
            role="Volunteer",
        )

    def test_submit_report(self):
        self.client.force_authenticate(user=self.citizen)
        url = reverse("reports-list-create")
        payload = {
            "reported_user": str(self.reported.user_id),
            "category": "no_show",
            "description": "Collector did not arrive at the scheduled time.",
        }
        response = self.client.post(url, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["category"], "no_show")
        self.assertEqual(response.data["status"], "pending")
        self.assertEqual(Report.objects.count(), 1)
