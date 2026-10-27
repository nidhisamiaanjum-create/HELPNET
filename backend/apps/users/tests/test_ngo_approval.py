
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from apps.users.models import UserProfile

User = get_user_model()


class NGOApprovalTests(APITestCase):
    def setUp(self):
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
            {"approval_status": "rejected"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.ngo_profile.refresh_from_db()
        self.assertEqual(
            self.ngo_profile.ngo_approval_status,
            UserProfile.NGOApprovalStatus.REJECTED,
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
