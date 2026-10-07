from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient
import csv
import io
import tempfile

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
        for path in ("/volunteer-opportunities/", "/create-opportunity/", "/volunteer-profile/", "/volunteer-attendance/", "/volunteer-search/", "/admin-volunteers/"):
            page = page_client.get(path)
            self.assertEqual(page.status_code, 200)
            self.assertIn(b"HELPNET", page.content)


class SprintFourCompletionTests(TestCase):
    def setUp(self):
        self.ngo = User.objects.create_user(phone_number="01000000101", email="ngo2@example.test", full_name="NGO Two", password="test-password-123", role="NGO")
        self.citizen = User.objects.create_user(phone_number="01000000102", email="citizen2@example.test", full_name="Citizen Two", password="test-password-123", role="Citizen")
        self.volunteer = User.objects.create_user(phone_number="01000000103", email="private-volunteer@example.test", full_name="Volunteer One", password="test-password-123", role="Volunteer")
        self.other_volunteer = User.objects.create_user(phone_number="01000000104", email="private-other@example.test", full_name="Volunteer Two", password="test-password-123", role="Volunteer")
        self.event = VolunteerOpportunity.objects.create(title="Food Support", description="Pack food", date="2026-10-20", location="Dhaka", required_volunteers=1, coordinator=self.ngo)
        self.client = APIClient()

    def test_ngo_can_post_citizen_is_refused_and_signup_capacity_enforced(self):
        self.client.force_authenticate(self.citizen)
        payload = {"title": "Citizen event", "description": "No", "date": "2026-10-21", "location": "Dhaka", "required_volunteers": 2}
        self.assertEqual(self.client.post("/api/volunteer/opportunities/", payload, format="json").status_code, 403)
        self.client.force_authenticate(self.ngo)
        self.assertEqual(self.client.post("/api/volunteer/opportunities/", payload, format="json").status_code, 201)
        self.client.force_authenticate(self.volunteer)
        url = f"/api/volunteer/opportunities/{self.event.pk}/signup/"
        self.assertEqual(self.client.post(url, {}, format="json").status_code, 201)
        self.assertEqual(self.client.post(url, {}, format="json").status_code, 400)
        self.client.force_authenticate(self.other_volunteer)
        self.assertEqual(self.client.post(url, {}, format="json").status_code, 400)

    @override_settings(MEDIA_ROOT=tempfile.gettempdir())
    def test_profile_save_and_certificate_upload_validation(self):
        self.client.force_authenticate(self.volunteer)
        saved = self.client.put("/api/volunteer/profile/", {"skills": "First aid", "availability": "Weekends", "location": "Dhaka", "blood_group": "O+"}, format="json")
        self.assertEqual(saved.status_code, 200)
        upload_url = "/api/volunteer/profile/documents/"
        uploaded = self.client.post(upload_url, {"file": SimpleUploadedFile("first-aid.pdf", b"%PDF-1.4 certificate")}, format="multipart")
        self.assertEqual(uploaded.status_code, 201)
        self.assertEqual(self.client.get(upload_url).data["data"][0]["original_name"], "first-aid.pdf")
        rejected = self.client.post(upload_url, {"file": SimpleUploadedFile("script.exe", b"no")}, format="multipart")
        self.assertEqual(rejected.status_code, 400)
        from .models import VolunteerProfile
        VolunteerProfile.objects.get(user=self.volunteer).documents.first().file.delete(save=False)

    def test_search_single_and_combined_participation_filters_and_csv_privacy(self):
        from .models import VolunteerProfile
        VolunteerProfile.objects.create(user=self.volunteer, skills="First aid, cooking", availability="Weekends", location="Dhaka", blood_group="O+", supporting_certificates="private certificate")
        VolunteerProfile.objects.create(user=self.other_volunteer, skills="Teaching", availability="Weekdays", location="Chittagong", blood_group="A+", supporting_certificates="another private certificate")
        VolunteerSignup.objects.create(volunteer=self.volunteer, event=self.event)
        self.client.force_authenticate(self.ngo)
        single = self.client.get("/api/volunteer/search/?skills=first%20aid")
        self.assertEqual([row["full_name"] for row in single.data["data"]], ["Volunteer One"])
        combined = self.client.get("/api/volunteer/search/?skills=first&availability=weekends&location=dhaka&participation_history=yes")
        self.assertEqual([row["full_name"] for row in combined.data["data"]], ["Volunteer One"])
        none = self.client.get("/api/volunteer/search/?participation_history=no")
        self.assertEqual([row["full_name"] for row in none.data["data"]], ["Volunteer Two"])

        admin = User.objects.create_user(phone_number="01000000105", email="admin2@example.test", full_name="Admin Two", password="test-password-123", role="Admin")
        self.client.force_authenticate(admin)
        response = self.client.get("/api/admin/volunteers/export/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/csv; charset=utf-8")
        rows = list(csv.reader(io.StringIO(response.content.decode("utf-8-sig"))))
        self.assertEqual(rows[0], ["Full name", "Skills", "Availability", "Location", "Signup count", "Completed events"])
        export_rows = {row[0]: row for row in rows[1:]}
        self.assertIn("Volunteer One", export_rows)
        csv_text = response.content.decode("utf-8")
        for private in ("private-volunteer@example.test", "01000000103", "O+", "private certificate"):
            self.assertNotIn(private, csv_text)
        self.client.force_authenticate(self.citizen)
        self.assertEqual(self.client.get("/api/admin/volunteers/export/").status_code, 403)

    def test_attendance_timestamps_are_recorded_once_and_cannot_be_overwritten(self):
        VolunteerSignup.objects.create(volunteer=self.volunteer, event=self.event)
        self.client.force_authenticate(self.ngo)
        url = f"/api/volunteer/opportunities/{self.event.pk}/attendance/"
        payload = {"volunteer_id": str(self.volunteer.user_id), "action": "check_in"}
        first = self.client.post(url, payload, format="json")
        original_check_in = first.data["data"]["check_in_time"]
        self.assertEqual(first.status_code, 200)
        self.assertEqual(self.client.post(url, payload, format="json").status_code, 400)
        check_out = self.client.post(url, {**payload, "action": "check_out"}, format="json")
        self.assertEqual(check_out.status_code, 200)
        self.assertEqual(check_out.data["data"]["check_in_time"], original_check_in)
        original_check_out = check_out.data["data"]["check_out_time"]
        self.assertEqual(self.client.post(url, {**payload, "action": "check_out"}, format="json").status_code, 400)
        self.assertEqual(VolunteerAttendance.objects.get(event=self.event, volunteer=self.volunteer).check_out_time.isoformat().replace("+00:00", "Z"), original_check_out)
