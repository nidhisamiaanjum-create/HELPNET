from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from .models import VolunteerAttendance, VolunteerOpportunity, VolunteerSignup


User = get_user_model()


class VolunteerMessageAndCertificateTests(TestCase):
    def setUp(self):
        self.coordinator = User.objects.create_user(
            phone_number="01000000001",
            email="coordinator@example.test",
            full_name="Event Coordinator",
            password="test-password-123",
            role="NGO",
        )
        self.volunteer = User.objects.create_user(
            phone_number="01000000002",
            email="volunteer@example.test",
            full_name="Test Volunteer",
            password="test-password-123",
            role="Volunteer",
        )
        self.outsider = User.objects.create_user(
            phone_number="01000000003",
            email="outsider@example.test",
            full_name="Outside Volunteer",
            password="test-password-123",
            role="Volunteer",
        )
        self.event = VolunteerOpportunity.objects.create(
            title="Community Cleanup",
            description="Clean the local park.",
            date="2026-10-01",
            location="Dhaka",
            required_volunteers=5,
            coordinator=self.coordinator,
        )
        VolunteerSignup.objects.create(volunteer=self.volunteer, event=self.event)
        self.client = APIClient()

    def test_event_participants_send_and_reload_messages(self):
        self.client.force_authenticate(self.volunteer)
        url = f"/api/volunteer/opportunities/{self.event.pk}/messages/"

        sent = self.client.post(url, {"message": "I can bring supplies."}, format="json")
        self.assertEqual(sent.status_code, 201)
        self.assertEqual(sent.data["data"]["sender_name"], self.volunteer.full_name)

        # A new GET, equivalent to reloading the messages page, returns the saved message.
        reloaded = self.client.get(url)
        self.assertEqual(reloaded.status_code, 200)
        self.assertEqual(reloaded.data["data"][0]["message"], "I can bring supplies.")

        self.client.force_authenticate(self.coordinator)
        self.assertEqual(self.client.get(url).status_code, 200)
        coordinator_message = self.client.post(url, {"message": "Please arrive at 9 AM."}, format="json")
        self.assertEqual(coordinator_message.status_code, 201)

        self.client.force_authenticate(self.outsider)
        self.assertEqual(self.client.get(url).status_code, 403)
        self.assertEqual(self.client.post(url, {"message": "Not a member."}, format="json").status_code, 403)

    def test_coordinator_issues_correct_certificate_and_downloads_pdf(self):
        VolunteerAttendance.objects.create(
            volunteer=self.volunteer,
            event=self.event,
            check_in_time=timezone.now(),
            check_out_time=timezone.now(),
        )
        self.client.force_authenticate(self.coordinator)
        url = f"/api/volunteer/opportunities/{self.event.pk}/certificates/"
        issued = self.client.post(url, {"volunteer_id": str(self.volunteer.user_id)}, format="json")

        self.assertEqual(issued.status_code, 201)
        data = issued.data["data"]
        self.assertEqual(data["volunteer_name"], self.volunteer.full_name)
        self.assertEqual(data["event_name"], self.event.title)
        self.assertEqual(data["coordinator_name"], self.coordinator.full_name)

        pdf = self.client.get(f"/api/volunteer/certificates/{data['id']}/pdf/")
        self.assertEqual(pdf.status_code, 200)
        self.assertEqual(pdf["Content-Type"], "application/pdf")
        self.assertIn("attachment", pdf["Content-Disposition"])
        self.assertTrue(pdf.content.startswith(b"%PDF"))

    def test_certificate_requires_completed_attendance_and_download_is_private(self):
        self.client.force_authenticate(self.coordinator)
        issue_url = f"/api/volunteer/opportunities/{self.event.pk}/certificates/"
        incomplete = self.client.post(issue_url, {"volunteer_id": str(self.volunteer.user_id)}, format="json")
        self.assertEqual(incomplete.status_code, 400)

        VolunteerAttendance.objects.create(
            volunteer=self.volunteer,
            event=self.event,
            check_in_time=timezone.now(),
            check_out_time=timezone.now(),
        )
        issued = self.client.post(issue_url, {"volunteer_id": str(self.volunteer.user_id)}, format="json")
        certificate_id = issued.data["data"]["id"]

        self.client.force_authenticate(self.outsider)
        self.assertEqual(self.client.get(f"/api/volunteer/certificates/{certificate_id}/pdf/").status_code, 403)

        self.client.force_authenticate(self.volunteer)
        self.assertEqual(self.client.get(f"/api/volunteer/certificates/{certificate_id}/pdf/").status_code, 200)

    def test_message_and_certificate_apis_require_authentication(self):
        message_url = f"/api/volunteer/opportunities/{self.event.pk}/messages/"
        certificate_url = f"/api/volunteer/opportunities/{self.event.pk}/certificates/"
        self.assertEqual(self.client.get(message_url).status_code, 401)
        self.assertEqual(self.client.post(message_url, {"message": "Unauthenticated."}, format="json").status_code, 401)
        self.assertEqual(self.client.post(certificate_url, {"volunteer_id": str(self.volunteer.user_id)}, format="json").status_code, 401)

    def test_my_events_returns_joined_or_coordinated_events(self):
        self.client.force_authenticate(self.volunteer)
        joined = self.client.get("/api/volunteer/my-events/")
        self.assertEqual(joined.status_code, 200)
        self.assertEqual([event["id"] for event in joined.data["data"]], [self.event.pk])

        self.client.force_authenticate(self.coordinator)
        coordinated = self.client.get("/api/volunteer/my-events/?coordinated=true")
        self.assertEqual(coordinated.status_code, 200)
        self.assertEqual([event["id"] for event in coordinated.data["data"]], [self.event.pk])

    def test_opportunity_browse_signup_duplicate_and_coordinator_management(self):
        self.client.force_authenticate(self.volunteer)
        browse = self.client.get("/api/volunteer/opportunities/")
        self.assertEqual(browse.status_code, 200)
        self.assertIn(self.event.pk, [event["id"] for event in browse.data["data"]])
        # Existing signup is returned as a duplicate error instead of a server error.
        duplicate = self.client.post(f"/api/volunteer/opportunities/{self.event.pk}/signup/", {}, format="json")
        self.assertEqual(duplicate.status_code, 400)

        self.client.force_authenticate(self.coordinator)
        created = self.client.post("/api/volunteer/opportunities/", {
            "title": "Food distribution",
            "description": "Prepare and distribute food packages.",
            "date": "2026-10-15",
            "location": "Dhaka",
            "required_volunteers": 4,
        }, format="json")
        self.assertEqual(created.status_code, 201)
        new_event_id = created.data["data"]["id"]
        closed = self.client.patch(f"/api/volunteer/opportunities/{new_event_id}/", {"status": "Closed"}, format="json")
        self.assertEqual(closed.status_code, 200)
        self.assertEqual(closed.data["data"]["id"], new_event_id)
        managed = self.client.get("/api/volunteer/my-events/?coordinated=true")
        self.assertIn(new_event_id, [event["id"] for event in managed.data["data"]])

    @override_settings(ALLOWED_HOSTS=["localhost", "testserver"])
    def test_coordinator_attendance_and_page_routes(self):
        self.client.force_authenticate(self.coordinator)
        url = f"/api/volunteer/opportunities/{self.event.pk}/attendance/"
        attendance = self.client.get(url)
        self.assertEqual(attendance.status_code, 200)
        self.assertEqual(str(attendance.data["data"][0]["volunteer"]), str(self.volunteer.user_id))
        checked_in = self.client.post(url, {"volunteer_id": str(self.volunteer.user_id), "action": "check_in"}, format="json")
        self.assertEqual(checked_in.status_code, 200)
        self.assertIsNotNone(checked_in.data["data"]["check_in_time"])
        checked_out = self.client.post(url, {"volunteer_id": str(self.volunteer.user_id), "action": "check_out"}, format="json")
        self.assertEqual(checked_out.status_code, 200)
        self.assertIsNotNone(checked_out.data["data"]["check_out_time"])

        self.client.force_authenticate(self.volunteer)
        self.assertEqual(self.client.get(url).status_code, 403)

        page_client = Client(HTTP_HOST="localhost")
        for path in ("/volunteer-opportunities/", "/volunteer-attendance/"):
            page = page_client.get(path)
            self.assertEqual(page.status_code, 200)
