import tempfile
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from rest_framework.test import APIRequestFactory, APITestCase

from apps.users.models import NGOVerificationDocument, UserProfile
from apps.users.permissions import IsNGOUser


User = get_user_model()


class NGOVerificationTests(APITestCase):
    def setUp(self):
        self.private_root = tempfile.TemporaryDirectory()
        self.addCleanup(self.private_root.cleanup)
        self.private_media_override = override_settings(
            PRIVATE_MEDIA_ROOT=Path(self.private_root.name)
        )
        self.private_media_override.enable()
        self.addCleanup(self.private_media_override.disable)
        storage = NGOVerificationDocument._meta.get_field("file").storage
        original_location = storage._location
        original_base_location = storage.__dict__.get("base_location")
        original_cached_location = storage.__dict__.get("location")
        storage._location = Path(self.private_root.name)
        storage.__dict__.pop("location", None)
        storage.__dict__.pop("base_location", None)

        def restore_storage_location():
            storage._location = original_location
            storage.__dict__.pop("location", None)
            storage.__dict__.pop("base_location", None)
            if original_base_location is not None:
                storage.__dict__["base_location"] = original_base_location
            if original_cached_location is not None:
                storage.__dict__["location"] = original_cached_location

        self.addCleanup(restore_storage_location)

        self.owner = User.objects.create_user(
            phone_number="01722220001",
            email="ngo-verification-owner@example.test",
            full_name="NGO Representative",
            password="pass-word-123",
            role="NGO",
        )
        self.profile = UserProfile.objects.create(
            user=self.owner,
            profile_type=UserProfile.Type.NGO,
            display_name="Community Support",
            ngo_approval_status=UserProfile.NGOApprovalStatus.PENDING,
        )
        self.owner.active_profile = self.profile
        self.owner.save(update_fields=["active_profile"])
        self.owner.refresh_from_db()
        self.submit_url = (
            f"/api/auth/profiles/{self.profile.id}/ngo-verification/"
        )
        self.client.force_authenticate(self.owner)

    @staticmethod
    def valid_certificate(name="registration.pdf"):
        return SimpleUploadedFile(
            name,
            b"%PDF-1.7\nregistration document",
            content_type="application/pdf",
        )

    def submission_data(self, certificate=None, **files):
        data = {
            "organization_name": "Community Support",
            "registration_number": "NGO-2026-001",
            "organization_address": "Dhaka, Bangladesh",
            "official_contact_email": "contact@community.example",
            "contact_phone": "01722220002",
            "representative_name": "NGO Representative",
        }
        if certificate is not None:
            data["registration_certificate"] = certificate
        data.update(files)
        return data

    def submit(self, certificate=None, **files):
        return self.client.post(
            self.submit_url,
            self.submission_data(certificate, **files),
            format="multipart",
        )

    def test_owner_submits_required_ngo_information_and_private_certificate(self):
        response = self.submit(self.valid_certificate())
        self.assertEqual(response.status_code, 200, response.data)
        self.profile.refresh_from_db()
        self.assertEqual(
            self.profile.ngo_verification_status,
            UserProfile.NGOVerificationStatus.PENDING,
        )
        self.assertEqual(self.profile.ngo_registration_number, "NGO-2026-001")
        self.assertIsNotNone(self.profile.ngo_submitted_at)
        self.assertEqual(
            NGOVerificationDocument.objects.filter(profile=self.profile).count(),
            1,
        )
        document = NGOVerificationDocument.objects.get(profile=self.profile)
        self.assertTrue(
            Path(document.file.path).is_relative_to(Path(self.private_root.name)),
            f"{document.file.path} is outside {self.private_root.name}",
        )
        with self.assertRaises(ValueError):
            _ = document.file.url
        self.assertEqual(
            response.data["data"]["documents"][0]["name"],
            "registration.pdf",
        )

    def test_optional_documents_are_not_required(self):
        response = self.submit(self.valid_certificate())
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(len(response.data["data"]["documents"]), 1)

    def test_optional_png_is_accepted_and_document_size_limit_is_enforced(self):
        response = self.submit(
            self.valid_certificate(),
            supporting_documents=[
                SimpleUploadedFile(
                    "supporting.png",
                    b"\x89PNG\r\n\x1a\nimage",
                    content_type="image/png",
                )
            ],
        )
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(len(response.data["data"]["documents"]), 2)

        self.profile.ngo_verification_status = (
            UserProfile.NGOVerificationStatus.REJECTED
        )
        self.profile.save(update_fields=["ngo_verification_status"])
        too_large = SimpleUploadedFile(
            "large.pdf",
            b"%PDF-1.7\n" + (b"x" * (10 * 1024 * 1024)),
            content_type="application/pdf",
        )
        oversized_response = self.submit(too_large)
        self.assertEqual(oversized_response.status_code, 400)

    def test_registration_certificate_is_required(self):
        response = self.submit()
        self.assertEqual(response.status_code, 400)
        self.assertEqual(NGOVerificationDocument.objects.count(), 0)

    def test_rejected_application_can_replace_registration_document(self):
        self.submit(self.valid_certificate())
        original = NGOVerificationDocument.objects.get(profile=self.profile)
        self.profile.ngo_verification_status = (
            UserProfile.NGOVerificationStatus.REJECTED
        )
        self.profile.save(update_fields=["ngo_verification_status"])

        response = self.submit(self.valid_certificate("updated-registration.pdf"))
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(
            NGOVerificationDocument.objects.filter(profile=self.profile).count(),
            1,
        )
        replacement = NGOVerificationDocument.objects.get(profile=self.profile)
        self.assertNotEqual(replacement.id, original.id)
        self.assertEqual(replacement.original_name, "updated-registration.pdf")

    def test_additional_documents_request_requires_a_new_upload(self):
        self.submit(self.valid_certificate())
        self.profile.ngo_verification_status = (
            UserProfile.NGOVerificationStatus.ADDITIONAL_DOCUMENTS_REQUIRED
        )
        self.profile.save(update_fields=["ngo_verification_status"])

        missing_document = self.submit()
        self.assertEqual(missing_document.status_code, 400)

        supporting = SimpleUploadedFile(
            "authorization.pdf",
            b"%PDF-1.7\nauthorization",
            content_type="application/pdf",
        )
        resubmitted = self.submit(authorization_letters=[supporting])
        self.assertEqual(resubmitted.status_code, 200, resubmitted.data)
        self.profile.refresh_from_db()
        self.assertEqual(
            self.profile.ngo_verification_status,
            UserProfile.NGOVerificationStatus.PENDING,
        )

    def test_invalid_document_type_and_content_are_rejected(self):
        invalid_extension = self.submit(
            SimpleUploadedFile(
                "registration.exe",
                b"%PDF-1.7",
                content_type="application/pdf",
            )
        )
        self.assertEqual(invalid_extension.status_code, 400)

        invalid_signature = self.submit(
            SimpleUploadedFile(
                "registration.pdf",
                b"not a pdf document",
                content_type="application/pdf",
            )
        )
        self.assertEqual(invalid_signature.status_code, 400)
        self.assertEqual(NGOVerificationDocument.objects.count(), 0)

    def test_documents_are_private_to_owner_and_superuser(self):
        self.submit(self.valid_certificate())
        document = NGOVerificationDocument.objects.get(profile=self.profile)
        url = f"/api/auth/ngo-verification-documents/{document.id}/"

        owner_response = self.client.get(url)
        self.assertEqual(owner_response.status_code, 200)
        self.assertEqual(
            owner_response["Content-Disposition"],
            'attachment; filename="registration.pdf"',
        )
        self.assertEqual(
            b"".join(owner_response.streaming_content),
            b"%PDF-1.7\nregistration document",
        )
        owner_response.close()

        outsider = User.objects.create_user(
            phone_number="01722220003",
            email="ngo-verification-outsider@example.test",
            full_name="Other Person",
            password="pass-word-123",
        )
        self.client.force_authenticate(outsider)
        self.assertEqual(self.client.get(url).status_code, 403)

        admin = User.objects.create_superuser(
            phone_number="01722220004",
            email="ngo-verification-admin@example.test",
            full_name="Admin",
            password="pass-word-123",
        )
        self.client.force_authenticate(admin)
        admin_response = self.client.get(url)
        self.assertEqual(admin_response.status_code, 200)
        admin_response.close()

    def test_admin_can_review_statuses_and_reason_and_approve_without_verifying_nid(self):
        self.submit(self.valid_certificate())
        admin = User.objects.create_superuser(
            phone_number="01722220005",
            email="ngo-status-admin@example.test",
            full_name="Review Admin",
            password="pass-word-123",
        )
        self.client.force_authenticate(admin)
        approval_url = (
            f"/api/auth/ngo-profiles/{self.profile.id}/approval/"
        )
        pending_list = self.client.get("/api/auth/ngo-profiles/pending/")
        self.assertEqual(pending_list.status_code, 200)
        application = pending_list.data["data"][0]
        self.assertEqual(
            application["ngo_registration_number"],
            "NGO-2026-001",
        )
        self.assertEqual(len(application["documents"]), 1)
        self.assertIn("download_url", application["documents"][0])

        for state in (
            UserProfile.NGOVerificationStatus.UNDER_REVIEW,
            UserProfile.NGOVerificationStatus.ADDITIONAL_DOCUMENTS_REQUIRED,
            UserProfile.NGOVerificationStatus.REJECTED,
        ):
            payload = {"verification_status": state}
            if state != UserProfile.NGOVerificationStatus.UNDER_REVIEW:
                payload["review_reason"] = "Please provide updated documents."
            response = self.client.patch(approval_url, payload, format="json")
            self.assertEqual(response.status_code, 200, response.data)
            self.profile.refresh_from_db()
            self.assertEqual(self.profile.ngo_verification_status, state)
            self.assertIsNotNone(self.profile.ngo_reviewed_at)

        approved = self.client.patch(
            approval_url,
            {"verification_status": "approved"},
            format="json",
        )
        self.assertEqual(approved.status_code, 200, approved.data)
        self.profile.refresh_from_db()
        self.owner.refresh_from_db()
        self.assertEqual(
            self.profile.ngo_verification_status,
            UserProfile.NGOVerificationStatus.APPROVED,
        )
        self.assertEqual(
            self.profile.ngo_approval_status,
            UserProfile.NGOApprovalStatus.APPROVED,
        )
        request = APIRequestFactory().get("/")
        request.user = self.owner
        self.assertTrue(IsNGOUser().has_permission(request, None))
        self.assertFalse(self.owner.is_verified)

    def test_ngo_features_require_approved_active_ngo_profile(self):
        request = APIRequestFactory().get("/")
        request.user = self.owner
        permission = IsNGOUser()
        self.assertFalse(permission.has_permission(request, None))

        self.profile.ngo_verification_status = (
            UserProfile.NGOVerificationStatus.APPROVED
        )
        self.profile.save(update_fields=["ngo_verification_status"])
        self.owner.refresh_from_db()
        request.user = self.owner
        self.assertTrue(permission.has_permission(request, None))

        self.profile.status = UserProfile.Status.INACTIVE
        self.profile.save(update_fields=["status"])
        self.owner.refresh_from_db()
        request.user = self.owner
        self.assertFalse(permission.has_permission(request, None))

    def test_rejection_and_additional_document_request_require_reason(self):
        admin = User.objects.create_superuser(
            phone_number="01722220006",
            email="ngo-reason-admin@example.test",
            full_name="Reason Admin",
            password="pass-word-123",
        )
        self.client.force_authenticate(admin)
        url = f"/api/auth/ngo-profiles/{self.profile.id}/approval/"
        for state in ("rejected", "additional_documents_required"):
            response = self.client.patch(
                url,
                {"verification_status": state},
                format="json",
            )
            self.assertEqual(response.status_code, 400)

    def test_inactive_or_unselected_ngo_cannot_submit(self):
        self.owner.active_profile = None
        self.owner.save(update_fields=["active_profile"])
        self.assertEqual(self.submit(self.valid_certificate()).status_code, 400)
