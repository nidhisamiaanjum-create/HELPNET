import importlib
import tempfile

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.apps import apps
from types import SimpleNamespace
from rest_framework.test import APITestCase
from unittest.mock import patch
from rest_framework_simplejwt.tokens import RefreshToken

from apps.ratings.models import Rating
from apps.reports.models import Report
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

	def test_registration_creates_citizen_profile_without_blood_donor_profile(self):
		self.client.credentials()
		response = self.client.post(
			"/api/auth/register/",
			{
				"full_name": "Registered Donor",
				"email": "registered-donor@example.com",
				"phone_number": "01720000006",
				"password": "password123",
				"location": "Dhaka",
				"account_type": "citizen",
			},
			format="json",
		)

		self.assertEqual(response.status_code, 201)
		registered = User.objects.get(email="registered-donor@example.com")
		# Registration creates a citizen/NGO account profile, not a blood donor profile.
		self.assertEqual(registered.profiles.count(), 1)
		self.assertEqual(registered.active_profile.profile_type, "citizen")
		self.assertFalse(DonorProfile.objects.filter(user=registered).exists())
		self.assertFalse(
			registered.profiles.filter(profile_type="blood_donor").exists()
		)

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

	def test_supporting_document_is_private_to_requester_and_admin(self):
		upload = SimpleUploadedFile(
			"supporting-document.pdf",
			b"%PDF-1.7\nprivate supporting document",
			content_type="application/pdf",
		)
		self.authenticate(self.requester)
		created = self.client.post(
			"/api/blood/requests/",
			{
				"blood_group": "O+",
				"area": "Dhaka",
				"hospital": "Dhaka Medical College",
				"supporting_document": upload,
			},
			format="multipart",
		)
		self.assertEqual(created.status_code, 201, created.data)
		request_id = created.data["data"]["id"]
		document_url = created.data["data"]["supporting_document"]
		self.assertEqual(
			document_url,
			f"/api/blood/requests/{request_id}/document/",
		)

		blood_request = BloodRequest.objects.get(pk=request_id)
		self.addCleanup(blood_request.supporting_document.delete, save=False)
		self.assertTrue(
			blood_request.supporting_document.path.startswith(
				str(settings.PRIVATE_MEDIA_ROOT)
			)
		)

		self.authenticate(self.other_donor)
		listed = self.client.get("/api/blood/requests/")
		self.assertEqual(listed.status_code, 200)
		self.assertIsNone(listed.data["data"][0]["supporting_document"])
		self.assertEqual(self.client.get(document_url).status_code, 403)

		self.authenticate(self.requester)
		downloaded = self.client.get(document_url)
		self.assertEqual(downloaded.status_code, 200)
		self.assertEqual(
			b"".join(downloaded.streaming_content),
			b"%PDF-1.7\nprivate supporting document",
		)

		admin = self.make_user("01720000007", "admin@example.com", "Admin")
		admin.is_superuser = True
		admin.is_staff = True
		admin.save()
		self.authenticate(admin)
		admin_download = self.client.get(document_url)
		self.assertEqual(admin_download.status_code, 200)
		b"".join(admin_download.streaming_content)

	def test_supporting_document_rejects_mismatched_file_content(self):
		self.authenticate(self.requester)
		response = self.client.post(
			"/api/blood/requests/",
			{
				"blood_group": "O+",
				"area": "Dhaka",
				"hospital": "Dhaka Medical College",
				"supporting_document": SimpleUploadedFile(
					"not-a-pdf.pdf",
					b"not a PDF",
					content_type="application/pdf",
				),
			},
			format="multipart",
		)
		self.assertEqual(response.status_code, 400)
		self.assertFalse(BloodRequest.objects.exists())

	def test_migration_moves_existing_documents_to_private_storage(self):
		migration = importlib.import_module(
			"apps.blood.migrations.0004_private_blood_request_documents"
		)
		with tempfile.TemporaryDirectory() as public_root, tempfile.TemporaryDirectory() as private_root:
			public_storage = FileSystemStorage(location=public_root)
			source_name = "blood/supporting_documents/legacy-proof.pdf"
			public_storage.save(source_name, SimpleUploadedFile("legacy-proof.pdf", b"%PDF-1.7\nlegacy"))
			blood_request = BloodRequest.objects.create(
				requester=self.requester,
				blood_group="O+",
				area="Dhaka",
				hospital="Dhaka Medical College",
				supporting_document=source_name,
			)

			with patch("django.conf.settings.MEDIA_ROOT", public_root), patch(
				"django.conf.settings.PRIVATE_MEDIA_ROOT", private_root
			):
				migration.move_documents_to_private_storage(
					apps,
					SimpleNamespace(connection=SimpleNamespace(alias="default")),
				)

			blood_request.refresh_from_db()
			private_storage = FileSystemStorage(location=private_root)
			self.assertTrue(private_storage.exists(blood_request.supporting_document.name))
			self.assertFalse(public_storage.exists(source_name))
			with private_storage.open(blood_request.supporting_document.name, "rb") as document:
				self.assertEqual(document.read(), b"%PDF-1.7\nlegacy")

	def test_authenticated_user_can_report_blood_request(self):
		created = self.create_request()
		request_id = created.data["data"]["id"]
		response = self.client.post(
			f"/api/blood/requests/{request_id}/reports/",
			{"description": "The request details appear suspicious."},
			format="json",
		)
		self.assertEqual(response.status_code, 201)
		report = Report.objects.get(pk=response.data["data"]["id"])
		self.assertEqual(report.reporter, self.requester)
		self.assertEqual(report.reported_user, self.requester)
		self.assertEqual(report.content_object, BloodRequest.objects.get(pk=request_id))
		self.assertEqual(report.description, "The request details appear suspicious.")

	def test_blood_screens_have_no_promotional_or_leaderboard_content(self):
		response = self.client.get("/blood-requests/")
		self.assertEqual(response.status_code, 200)
		self.assertNotContains(response, "leaderboard")
		self.assertNotContains(response, "advertisement")
		self.assertNotContains(response, "sponsored")

# Create your tests here.
