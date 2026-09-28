from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from .models import Rating

User = get_user_model()


class RatingTests(APITestCase):
    def setUp(self):
        self.citizen = User.objects.create_user(
            phone_number="01711115555",
            email="citizen_rater@example.com",
            full_name="Citizen Rater",
            password="password123",
            role="Citizen",
        )
        self.collector = User.objects.create_user(
            phone_number="01822226666",
            email="collector_rated@example.com",
            full_name="Collector Rated",
            password="password123",
            role="Volunteer",
        )

    def test_rate_collector_and_view_summary(self):
        self.client.force_authenticate(user=self.citizen)
        url = reverse("ratings-list-create")
        payload = {
            "rated_user": str(self.collector.user_id),
            "score": 5,
            "comment": "Quick and clean waste pickup!",
        }
        response = self.client.post(url, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        summary_url = reverse("user-rating-summary", kwargs={"user_id": self.collector.user_id})
        summary_res = self.client.get(summary_url)
        self.assertEqual(summary_res.status_code, status.HTTP_200_OK)
        self.assertEqual(summary_res.data["data"]["average_rating"], 5.0)
        self.assertEqual(summary_res.data["data"]["total_ratings"], 1)
        self.assertTrue(summary_res.data["data"]["user_has_rated"])

    def test_cannot_rate_oneself(self):
        self.client.force_authenticate(user=self.citizen)
        url = reverse("ratings-list-create")
        payload = {
            "rated_user": str(self.citizen.user_id),
            "score": 5,
        }
        response = self.client.post(url, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
