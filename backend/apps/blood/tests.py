from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.ratings.models import Rating
from .models import BloodRequest, DonationHistory, DonorProfile


User = get_user_model()


class BloodApiTests(APITestCase):
	def setUp(self):
		self.requester = self.make_user("01720000001", "requester@example.com", "Requester")
		self.donor = self.make_user("01720000002", "donor@example.com", "Matching Donor")
		self.other_donor = self.make_user("01720000003", "other@example.com", "Other Donor")
		self.authenticate(self.requester)

	def make_user(self, phone, email, name):
		return User.objects.create_user(
			phone_number=phone,
			email=email,
			full_name=name,
			password="password123",
		)

	def authenticate(self, user):
		token = RefreshToken.for_user(user).access_token
		self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

	def profile_url(self):
		return "/api/blood/donor-profile/"

	def create_profile(self, user, blood_group="O+", area="Dhaka", available=True):
		self.authenticate(user)
		response = self.client.put(
			self.profile_url(),
			{"blood_group": blood_group, "area": area, "is_available": available},
			format="json",
		)
		self.assertEqual(response.status_code, 200)
		return response

	def create_request(self, **overrides):
		data = {
			"blood_group": "O+",
			"area": "Dhaka",
			"hospital": "Dhaka Medical College",
			"details": "Urgent request",
		}
		data.update(overrides)
		self.authenticate(self.requester)
		response = self.client.post("/api/blood/requests/", data, format="json")
		self.assertEqual(response.status_code, 201)
		return response

	def test_user_can_register_as_a_blood_donor(self):
		self.client.credentials()
		response = self.client.post(
			"/api/auth/register/",
			{
				"full_name": "Registered Donor",
				"email": "registered-donor@example.com",
				"phone_number": "01720000006",
				"password": "password123",
				"role": "Blood Donor",
				"location": "Dhaka",
			},
			format="json",
		)

		self.assertEqual(response.status_code, 201)
		self.assertEqual(response.data["data"]["role"], "Blood Donor")

	def test_donor_profile_can_select_group_set_area_and_change_availability(self):
		response = self.create_profile(self.donor, available=True)
		self.assertEqual(response.data["data"]["blood_group"], "O+")
		self.assertEqual(response.data["data"]["area"], "Dhaka")
		self.assertTrue(response.data["data"]["is_available"])

		response = self.create_profile(self.donor, blood_group="A-", area="Khulna", available=False)
		self.assertEqual(response.data["data"]["blood_group"], "A-")
		self.assertEqual(response.data["data"]["area"], "Khulna")
		self.assertFalse(response.data["data"]["is_available"])

	def test_donor_cannot_change_another_donors_availability(self):
		self.create_profile(self.donor, "O+", "Dhaka", True)
		self.authenticate(self.other_donor)

		response = self.client.put(
			self.profile_url(),
			{
				"user_id": str(self.donor.user_id),
				"blood_group": "O+",
				"area": "Dhaka",
				"is_available": False,
			},
			format="json",
		)

		self.assertEqual(response.status_code, 200)
		self.assertFalse(response.data["data"]["is_available"])
		self.assertTrue(DonorProfile.objects.get(user=self.donor).is_available)

	def test_matching_requires_same_group_area_and_availability(self):
		self.create_profile(self.donor, "O+", "Dhaka", True)
		self.create_profile(self.other_donor, "A+", "Dhaka", True)
		unavailable = self.make_user("01720000004", "unavailable@example.com", "Unavailable")
		self.create_profile(unavailable, "O+", "Dhaka", False)
		wrong_area = self.make_user("01720000005", "area@example.com", "Wrong Area")
		self.create_profile(wrong_area, "O+", "Khulna", True)

		request_response = self.create_request()
		request_id = request_response.data["data"]["id"]
		self.authenticate(self.requester)
		response = self.client.get(f"/api/blood/requests/{request_id}/matches/")

		self.assertEqual(response.status_code, 200)
		self.assertEqual([item["user_id"] for item in response.data["data"]], [str(self.donor.user_id)])

	def test_donor_search_filters_available_group_and_area_and_includes_rating_data(self):
		self.create_profile(self.donor, "O+", "Dhaka", True)
		self.create_profile(self.other_donor, "A+", "Dhaka", True)
		self.authenticate(self.donor)
		Rating.objects.create(rater=self.requester, rated_user=self.donor, rating=5)

		response = self.client.get(
			"/api/blood/donors/",
			{"blood_group": "O+", "area": "Dhaka"},
		)

		self.assertEqual(response.status_code, 200)
		self.assertEqual(len(response.data["data"]), 1)
		self.assertEqual(response.data["data"][0]["user_id"], str(self.donor.user_id))
		self.assertTrue(response.data["data"][0]["is_available"])
		self.assertEqual(response.data["data"][0]["average_rating"], 5.0)
		self.assertEqual(response.data["data"][0]["rating_count"], 1)

	def test_request_can_be_fulfilled_only_by_owner_and_history_is_unique(self):
		self.create_profile(self.donor, "O+", "Dhaka", True)
		request_response = self.create_request()
		request_id = request_response.data["data"]["id"]

		self.authenticate(self.other_donor)
		forbidden = self.client.post(
			f"/api/blood/requests/{request_id}/complete/",
			{"donor_id": str(self.donor.user_id)},
			format="json",
		)
		self.assertEqual(forbidden.status_code, 403)

		self.authenticate(self.requester)
		completed = self.client.post(
			f"/api/blood/requests/{request_id}/complete/",
			{"donor_id": str(self.donor.user_id)},
			format="json",
		)
		self.assertEqual(completed.status_code, 200)
		self.assertEqual(DonationHistory.objects.filter(blood_request_id=request_id).count(), 1)
		self.assertFalse(DonorProfile.objects.get(user=self.donor).is_available)

		duplicate = self.client.post(
			f"/api/blood/requests/{request_id}/complete/",
			{"donor_id": str(self.donor.user_id)},
			format="json",
		)
		self.assertEqual(duplicate.status_code, 400)
		self.assertEqual(DonationHistory.objects.filter(blood_request_id=request_id).count(), 1)

	def test_request_owner_can_close_open_request(self):
		request_response = self.create_request()
		request_id = request_response.data["data"]["id"]
		response = self.client.post(f"/api/blood/requests/{request_id}/close/", format="json")

		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.data["data"]["status"], BloodRequest.Status.CLOSED)

	def test_donation_history_is_private_to_the_donor(self):
		self.create_profile(self.donor, "O+", "Dhaka", True)
		request_response = self.create_request()
		request_id = request_response.data["data"]["id"]
		self.client.post(
			f"/api/blood/requests/{request_id}/complete/",
			{"donor_id": str(self.donor.user_id)},
			format="json",
		)

		self.authenticate(self.donor)
		own_history = self.client.get("/api/blood/donations/")
		self.assertEqual(own_history.status_code, 200)
		self.assertEqual(len(own_history.data["data"]), 1)

		self.authenticate(self.other_donor)
		other_history = self.client.get("/api/blood/donations/")
		self.assertEqual(other_history.status_code, 200)
		self.assertEqual(other_history.data["data"], [])

	def test_unauthenticated_users_cannot_use_blood_apis(self):
		self.client.credentials()
		response = self.client.get("/api/blood/requests/")
		self.assertEqual(response.status_code, 401)

# Create your tests here.
