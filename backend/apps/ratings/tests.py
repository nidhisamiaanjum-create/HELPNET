from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Rating


User = get_user_model()


class RatingApiTests(APITestCase):
	def setUp(self):
		self.rater = User.objects.create_user(
			phone_number="01710000001",
			email="rater@example.com",
			full_name="Rater User",
			password="password123",
			is_verified=True,
		)
		self.rated_user = User.objects.create_user(
			phone_number="01710000002",
			email="rated@example.com",
			full_name="Rated User",
			password="password123",
			is_verified=True,
		)
		self.ratings_url = "/api/ratings/"
		self.user_ratings_url = f"/api/ratings/users/{self.rated_user.user_id}/"
		self.average_url = f"{self.user_ratings_url}average/"

	def authenticate(self):
		token = RefreshToken.for_user(self.rater).access_token
		self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

	def test_authenticated_user_can_create_rating(self):
		self.authenticate()

		response = self.client.post(
			self.ratings_url,
			{"rated_user": str(self.rated_user.user_id), "rating": 5, "comment": "Helpful"},
			format="json",
		)

		self.assertEqual(response.status_code, 201)
		self.assertEqual(response.data["data"]["rating"], 5)
		self.assertTrue(Rating.objects.filter(rater=self.rater, rated_user=self.rated_user).exists())

	def test_invalid_rating_is_rejected(self):
		self.authenticate()

		response = self.client.post(
			self.ratings_url,
			{"rated_user": str(self.rated_user.user_id), "rating": 6},
			format="json",
		)

		self.assertEqual(response.status_code, 400)
		self.assertIn("between 1 and 5", response.data["message"])

	def test_self_rating_is_rejected(self):
		self.authenticate()

		response = self.client.post(
			self.ratings_url,
			{"rated_user": str(self.rater.user_id), "rating": 4},
			format="json",
		)

		self.assertEqual(response.status_code, 400)
		self.assertIn("cannot rate yourself", response.data["message"])

	def test_average_and_existing_ratings_are_returned(self):
		second_rater = User.objects.create_user(
			phone_number="01710000003",
			email="second@example.com",
			full_name="Second Rater",
			password="password123",
		)
		Rating.objects.create(rater=self.rater, rated_user=self.rated_user, rating=5)
		Rating.objects.create(rater=second_rater, rated_user=self.rated_user, rating=3)
		self.authenticate()

		average_response = self.client.get(self.average_url)
		ratings_response = self.client.get(self.user_ratings_url)

		self.assertEqual(average_response.status_code, 200)
		self.assertEqual(average_response.data["data"]["average_rating"], 4.0)
		self.assertEqual(average_response.data["data"]["rating_count"], 2)
		self.assertEqual(ratings_response.status_code, 200)
		self.assertEqual(len(ratings_response.data["data"]), 2)

	def test_rating_endpoints_require_authentication(self):
		response = self.client.post(
			self.ratings_url,
			{"rated_user": str(self.rated_user.user_id), "rating": 5},
			format="json",
		)

		self.assertEqual(response.status_code, 401)

	def test_profile_response_preserves_verified_status_and_rating_aggregates(self):
		self.authenticate()

		response = self.client.get("/api/auth/me/")

		self.assertEqual(response.status_code, 200)
		self.assertTrue(response.data["data"]["is_verified"])
		self.assertIn("average_rating", response.data["data"])
		self.assertIn("rating_count", response.data["data"])

	def test_public_profile_includes_verification_and_rating_aggregates(self):
		self.authenticate()

		response = self.client.get(f"/api/users/{self.rated_user.user_id}/")

		self.assertEqual(response.status_code, 200)
		self.assertTrue(response.data["data"]["is_verified"])
		self.assertIn("average_rating", response.data["data"])
		self.assertIn("rating_count", response.data["data"])
		self.assertNotIn("email", response.data["data"])
from django.test import TestCase

# Create your tests here.
