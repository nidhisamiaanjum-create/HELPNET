
import tempfile
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from rest_framework.test import APITestCase

from apps.users.models import NGOVerificationDocument, UserProfile

User = get_user_model()


class NGOApprovalTests(APITestCase):
    def setUp(self):
        self.private_root = tempfile.TemporaryDirectory()
        self.addCleanup(self.private_root.cleanup)
        private_media_override = override_settings(
            PRIVATE_MEDIA_ROOT=Path(self.private_root.name)
        )
        private_media_override.enable()
        self.addCleanup(private_media_override.disable)
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
        self.ngo_user = User.objects.create_user(
            phone_number="01722223333",
            email="approval-ngo@example.test",
            full_name="Test NGO",
            password="test-password-123",
            role="NGO",
        )
        self.ngo_profile = UserProfile.objects.create(
            user=self.ngo_user,
            profile_type=UserProfile.Type.NGO,
            status=UserProfile.Status.ACTIVE,
            ngo_approval_status=UserProfile.NGOApprovalStatus.PENDING,
            display_name="Test NGO",
            ngo_registration_number="NGO-TEST-1",
            ngo_address="Dhaka",
            ngo_contact_email="contact@testngo.example",
            ngo_contact_phone="01722223334",
            ngo_representative_name="Test Representative",
        )
        NGOVerificationDocument.objects.create(
            profile=self.ngo_profile,
            document_type=(
                NGOVerificationDocument.DocumentType.REGISTRATION_CERTIFICATE
            ),
            file=SimpleUploadedFile(
                "registration.pdf",
                b"%PDF-1.7\nregistration",
                content_type="application/pdf",
            ),
            original_name="registration.pdf",
        )
        self.url = (
            f"/api/auth/ngo-profiles/{self.ngo_profile.id}/approval/"
        )

    def test_superuser_can_approve_ngo(self):
        admin = User.objects.create_superuser(
            phone_number="01722224444",
            email="approval-admin@example.test",
            full_name="Superuser",
            password="test-password-123",
        )
        self.client.force_authenticate(admin)

        response = self.client.patch(
            self.url,
            {"approval_status": "approved"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.ngo_profile.refresh_from_db()
        self.assertEqual(
            self.ngo_profile.ngo_approval_status,
            UserProfile.NGOApprovalStatus.APPROVED,
        )
        self.assertEqual(
            self.ngo_profile.ngo_verification_status,
            UserProfile.NGOVerificationStatus.APPROVED,
        )
        self.ngo_user.refresh_from_db()
        self.assertFalse(self.ngo_user.is_verified)

    def test_superuser_can_reject_ngo(self):
        admin = User.objects.create_superuser(
            phone_number="01722224445",
            email="approval-admin2@example.test",
            full_name="Superuser Two",
            password="test-password-123",
        )
        self.client.force_authenticate(admin)

        response = self.client.patch(
            self.url,
            {
                "approval_status": "rejected",
                "review_reason": "Registration documents do not match.",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.ngo_profile.refresh_from_db()
        self.assertEqual(
            self.ngo_profile.ngo_approval_status,
            UserProfile.NGOApprovalStatus.REJECTED,
        )
        self.assertEqual(
            self.ngo_profile.ngo_verification_status,
            UserProfile.NGOVerificationStatus.REJECTED,
        )

    def test_non_superuser_cannot_approve_ngo(self):
        ordinary_user = User.objects.create_user(
            phone_number="01722225555",
            email="ordinary@example.test",
            full_name="Ordinary User",
            password="test-password-123",
            is_staff=True,
        )
        self.client.force_authenticate(ordinary_user)

        response = self.client.patch(
            self.url,
            {"approval_status": "approved"},
            format="json",
        )

        self.assertEqual(response.status_code, 403)
        self.ngo_profile.refresh_from_db()
        self.assertEqual(
            self.ngo_profile.ngo_approval_status,
            UserProfile.NGOApprovalStatus.PENDING,
        )

    def test_invalid_approval_status_is_rejected(self):
        admin = User.objects.create_superuser(
            phone_number="01722226666",
            email="approval-admin3@example.test",
            full_name="Superuser Three",
            password="test-password-123",
        )
        self.client.force_authenticate(admin)

        response = self.client.patch(
            self.url,
            {"approval_status": "pending"},
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.ngo_profile.refresh_from_db()
        self.assertEqual(
            self.ngo_profile.ngo_approval_status,
            UserProfile.NGOApprovalStatus.PENDING,
        )
