from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.blood.models import DonorProfile
from .models import Notification

User = get_user_model()

class NotificationApiTests(APITestCase):
	def setUp(self):
		self.requester = self.make_user("01730000001", "requester@example.com", "Requester")
		self.matching_donor = self.make_user("01730000002", "matching@example.com", "Matching Donor")
		self.wrong_group = self.make_user("01730000003", "group@example.com", "Wrong Group")
		self.wrong_area = self.make_user("01730000004", "area@example.com", "Wrong Area")
		self.busy_donor = self.make_user("01730000005", "busy@example.com", "Busy Donor")
		self.unavailable_donor = self.make_user("01730000006", "unavailable@example.com", "Unavailable Donor")

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

	def create_profile(self, user, group, area, available):
		DonorProfile.objects.create(
			user=user,
			blood_group=group,
			area=area,
			is_available=available,
		)

	def create_request(self):
		self.authenticate(self.requester)
		response = self.client.post(
			"/api/blood/requests/",
			{
				"blood_group": "O+",
				"area": "Dhaka",
				"hospital": "Dhaka Medical College",
				"details": "Urgent",
			},
			format="json",
		)
		self.assertEqual(response.status_code, 201)

	def test_only_matching_available_donors_receive_alerts(self):
		self.create_profile(self.matching_donor, "O+", "Dhaka", True)
		self.create_profile(self.wrong_group, "A+", "Dhaka", True)
		self.create_profile(self.wrong_area, "O+", "Khulna", True)
		self.create_profile(self.busy_donor, "O+", "Dhaka", False)
		self.create_profile(self.unavailable_donor, "O+", "Dhaka", False)

		self.create_request()

		self.assertEqual(Notification.objects.filter(user=self.matching_donor).count(), 1)
		self.assertEqual(Notification.objects.filter(user=self.wrong_group).count(), 0)
		self.assertEqual(Notification.objects.filter(user=self.wrong_area).count(), 0)
		self.assertEqual(Notification.objects.filter(user=self.busy_donor).count(), 0)
		self.assertEqual(Notification.objects.filter(user=self.unavailable_donor).count(), 0)
		self.assertEqual(Notification.objects.filter(user=self.requester).count(), 0)

	def test_user_sees_only_own_notifications(self):
		own = Notification.objects.create(
			user=self.matching_donor,
			message="Own alert",
			notification_type="blood_request",
		)
		Notification.objects.create(
			user=self.wrong_group,
			message="Other alert",
			notification_type="blood_request",
		)
		self.authenticate(self.matching_donor)

		response = self.client.get("/api/notifications/")

		self.assertEqual(response.status_code, 200)
		self.assertEqual([item["id"] for item in response.data["data"]], [str(own.id)])

	def test_owner_can_mark_read_but_another_user_cannot(self):
		notification = Notification.objects.create(
			user=self.matching_donor,
			message="Own alert",
			notification_type="blood_request",
		)

		self.authenticate(self.wrong_group)
		forbidden = self.client.post(f"/api/notifications/{notification.id}/read/")
		self.assertEqual(forbidden.status_code, 404)

		self.authenticate(self.matching_donor)
		response = self.client.post(f"/api/notifications/{notification.id}/read/")

		self.assertEqual(response.status_code, 200)
		self.assertTrue(response.data["data"]["is_read"])
		notification.refresh_from_db()
		self.assertTrue(notification.is_read)

		second = Notification.objects.create(
			user=self.matching_donor,
			message="Second alert",
			notification_type="blood_request",
		)
		patch_response = self.client.patch(f"/api/notifications/{second.id}/read/")
		self.assertEqual(patch_response.status_code, 200)
		self.assertTrue(patch_response.data["data"]["is_read"])

	def test_notifications_require_authentication(self):
		response = self.client.get("/api/notifications/")
		self.assertEqual(response.status_code, 401)
from django.test import TestCase

# Create your tests here.
