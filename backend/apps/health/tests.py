from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework.test import APITestCase

from apps.ratings.models import Rating
from .models import HealthProfessional, HealthQuestion


User = get_user_model()


class HealthCommunityApiTests(APITestCase):
    
    def make_user(
        self,
        suffix,
        role="Citizen",
        is_verified=False,
        is_staff=False,
        is_superuser=False,
    ):
        return User.objects.create_user(
            phone_number=f"01700000{suffix}",
            email=f"health{suffix}@example.com",
            full_name=f"Health User {suffix}",
            password="test-password-123",
            role=role,
            is_verified=is_verified,
            is_staff=is_staff,
            is_superuser=is_superuser,
        )


    def test_question_list_create_detail_and_replies_include_trust_data(self):
        author = self.make_user("001")
        responder = self.make_user("002", is_verified=True)
        reviewer = self.make_user("003")
        Rating.objects.create(rater=reviewer, rated_user=responder, rating=5, comment="Helpful")

        self.client.force_authenticate(author)
        created = self.client.post(reverse("health-questions"), {
            "title": "Community health question",
            "description": "Question details",
            "category": "General",
        }, format="json")
        self.assertEqual(created.status_code, 201)
        question_id = created.data["data"]["id"]
        self.assertEqual(created.data["data"]["author"], author.user_id)

        listed = self.client.get(reverse("health-questions"))
        self.assertEqual(listed.status_code, 200)
        self.assertEqual(listed.data["data"][0]["title"], "Community health question")

        detail = self.client.get(reverse("health-question-detail", args=[question_id]))
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(detail.data["data"]["description"], "Question details")

        self.client.force_authenticate(responder)
        reply = self.client.post(reverse("health-question-replies", args=[question_id]), {
            "reply": "Community reply",
        }, format="json")
        self.assertEqual(reply.status_code, 201)
        self.assertTrue(reply.data["data"]["author_is_verified"])
        self.assertEqual(float(reply.data["data"]["author_average_rating"]), 5.0)
        self.assertEqual(reply.data["data"]["author_rating_count"], 1)
        self.assertTrue(HealthQuestion.objects.get(pk=question_id).replies.filter(pk=reply.data["data"]["id"]).exists())

        replies = self.client.get(reverse("health-question-replies", args=[question_id]))
        self.assertEqual(replies.status_code, 200)
        self.assertEqual(replies.data["data"][0]["reply"], "Community reply")

    def test_anonymous_health_actions_are_blocked(self):
        self.assertEqual(self.client.get(reverse("health-questions")).status_code, 401)
        self.assertEqual(self.client.post(reverse("health-questions"), {}, format="json").status_code, 401)

    def test_repeated_question_submission_and_legacy_duplicate_rows_are_deduplicated(self):
        author = self.make_user("006")
        self.client.force_authenticate(author)
        payload = {
            "title": "Back pain",
            "description": "What should I do?",
            "category": "General",
        }
        first = self.client.post(reverse("health-questions"), payload, format="json")
        second = self.client.post(reverse("health-questions"), payload, format="json")
        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(first.data["data"]["id"], second.data["data"]["id"])
        self.assertEqual(HealthQuestion.objects.filter(author=author).count(), 1)

        HealthQuestion.objects.create(author=author, **payload)
        listed = self.client.get(reverse("health-questions"))
        self.assertEqual(listed.status_code, 200)
        self.assertEqual(len(listed.data["data"]), 1)

    def test_only_admin_can_set_professional_verification(self):
        professional = HealthProfessional.objects.create(name="Directory listing", profession="Physician")
        citizen = self.make_user("004")
        self.client.force_authenticate(citizen)
        path = reverse("health-professional-verification", args=[professional.pk])
        self.assertEqual(self.client.patch(path, {"verification_status": "verified"}, format="json").status_code, 403)

        directory = self.client.get(reverse("health-professionals"))
        self.assertEqual(directory.status_code, 200)
        self.assertEqual(directory.data["data"], [])

        administrator = self.make_user("005", role="Admin",is_staff=True,is_superuser=True,)
        self.client.force_authenticate(administrator)
        verified = self.client.patch(path, {"verification_status": "verified"}, format="json")
        self.assertEqual(verified.status_code, 400)
        professional.refresh_from_db()
        self.assertEqual(professional.verification_status, "pending")

    @staticmethod
    def credential_file(content=b"%PDF-1.7\ncredential"):
        return SimpleUploadedFile("credential.pdf", content, content_type="application/pdf")

    def submit_professional_application(self, user, name="Dr Example", content=b"%PDF-1.7\ncredential"):
        self.client.force_authenticate(user)
        return self.client.post(reverse("health-professional-application"), {
            "name": name,
            "profession": "Physician",
            "specialization": "Community health",
            "location": "Dhaka",
            "contact": "+8801712345678",
            "credential_type": "Professional registration",
            "credential_number": "REG-12345",
            "credential_document": self.credential_file(content),
        }, format="multipart")

    def test_citizen_application_and_approved_only_directory(self):
        applicant = self.make_user("007")
        self.client.force_authenticate(applicant)
        invalid = self.client.post(reverse("health-professional-application"), {
            "name": "Dr Example", "profession": "Physician", "contact": "doctor@example.org",
            "credential_type": "Registration", "credential_number": "REG-1",
            "credential_document": self.credential_file(b"not a pdf"),
        }, format="multipart")
        self.assertEqual(invalid.status_code, 400)
        self.assertFalse(HealthProfessional.objects.filter(user=applicant).exists())

        submitted = self.submit_professional_application(applicant)
        self.assertEqual(submitted.status_code, 201, submitted.data)
        application = HealthProfessional.objects.get(user=applicant)
        self.addCleanup(application.credential_document.delete, save=False)
        self.assertEqual(submitted.data["data"]["status"], "pending")
        self.assertEqual(self.client.get(reverse("health-professionals")).data["data"], [])
        self.assertEqual(self.client.get(reverse("health-professional-application")).data["data"]["status"], "pending")
        self.assertEqual(self.submit_professional_application(applicant).status_code, 400)

        admin = self.make_user("008", role="Admin",is_staff=True,is_superuser=True,)
        self.client.force_authenticate(admin)
        approved = self.client.patch(reverse("health-professional-verification", args=[application.pk]), {"action": "approve"}, format="json")
        self.assertEqual(approved.status_code, 200, approved.data)
        directory = self.client.get(reverse("health-professionals"))
        self.assertEqual(len(directory.data["data"]), 1)
        self.assertTrue(directory.data["data"][0]["is_verified"])
        self.assertEqual(directory.data["data"][0]["contact"], "+8801712345678")

    def test_health_credential_review_and_document_are_admin_only(self):
        applicant = self.make_user("009")
        self.assertEqual(self.submit_professional_application(applicant).status_code, 201)
        application = HealthProfessional.objects.get(user=applicant)
        self.addCleanup(application.credential_document.delete, save=False)
        document_url = reverse("health-professional-credential-document", args=[application.pk])
        pending_url = reverse("health-professional-pending-applications")
        review_url = reverse("health-professional-verification", args=[application.pk])

        self.client.force_authenticate(applicant)
        self.assertEqual(self.client.get(pending_url).status_code, 403)
        self.assertEqual(self.client.get(document_url).status_code, 403)
        self.assertEqual(self.client.patch(review_url, {"action": "approve"}, format="json").status_code, 403)

        admin = self.make_user("010", role="Admin",is_staff=True,is_superuser=True,)
        self.client.force_authenticate(admin)
        pending = self.client.get(pending_url)
        self.assertEqual(pending.status_code, 200)
        self.assertEqual(pending.data["data"][0]["credential_number"], "REG-12345")
        self.assertEqual(pending.data["data"][0]["document_url"], document_url)
        document = self.client.get(document_url)
        self.assertEqual(document.status_code, 200)
        self.assertEqual(b"".join(document.streaming_content), b"%PDF-1.7\ncredential")

        self.assertEqual(self.client.patch(review_url, {"action": "reject"}, format="json").status_code, 400)
        rejected = self.client.patch(review_url, {"action": "reject", "reason": "Credential could not be confirmed."}, format="json")
        self.assertEqual(rejected.status_code, 200)
        self.client.force_authenticate(applicant)
        own_status = self.client.get(reverse("health-professional-application"))
        self.assertEqual(own_status.data["data"]["status"], "rejected")
        self.assertIn("could not be confirmed", own_status.data["data"]["rejection_reason"])

    def test_non_citizen_cannot_submit_or_read_an_application(self):
        volunteer = self.make_user("012", role="Volunteer")
        self.client.force_authenticate(volunteer)
        self.assertEqual(self.client.get(reverse("health-professional-application")).status_code, 403)
        response = self.client.post(reverse("health-professional-application"), {
            "name": "Volunteer applicant",
            "profession": "Physician",
            "contact": "doctor@example.org",
            "credential_type": "Registration",
            "credential_number": "REG-999",
            "credential_document": self.credential_file(),
        }, format="multipart")
        self.assertEqual(response.status_code, 403)

    def test_professional_page_has_bilingual_labels_and_exact_disclaimer(self):
        self.client.force_authenticate(self.make_user("011"))
        response = self.client.get("/health-professionals/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<html lang="bn">', html=False)
        self.assertContains(response, "Health professionals listed here are provided for discovery purposes only. HELPNET does not endorse any professional or provide medical diagnosis.")
        source = Path(__file__).resolve().parents[3] / "frontend" / "js" / "i18n.js"
        translations = source.read_text(encoding="utf-8")
        keys = (
            "healthProfessionalDisclaimer", "healthApplyTitle", "healthApplyInfo",
            "healthProfessionalName", "healthProfession", "healthSpecialization",
            "healthLocation", "healthContact", "healthCredentialType",
            "healthCredentialNumber", "healthCredentialDocument", "healthSubmitApplication",
            "healthStatusNotSubmitted", "healthStatusPending", "healthStatusApproved",
            "healthStatusRejected", "healthDirectoryLoading", "healthDirectoryEmpty",
            "healthDirectoryProfession", "healthDirectorySpecialization", "healthDirectoryLocation",
            "healthDirectoryContact", "healthVerifiedBadge", "healthOpenContact",
            "healthAdminApplications", "healthAdminEmpty", "healthCredentialNumberLabel",
            "healthViewCredential", "healthApprove", "healthReject", "healthConfirmReject",
            "healthRejectReason", "healthApplicationReviewed", "healthDocumentFailed",
        )
        for key in keys:
            self.assertEqual(translations.count(f"{key}:"), 2, key)

    def test_health_pages_show_non_endorsement_disclaimer(self):
        for url in ("/health-professionals/", "/health-questions/", "/create-health-question/", "/health-question-details/"):
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            expected_key = "healthProfessionalDisclaimer" if url == "/health-professionals/" else "healthDisclaimer"
            self.assertContains(response, f'data-i18n="{expected_key}"')
