from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from apps.users.models import UserProfile


User = get_user_model()


class AccountProfilesTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            phone_number="01711112222", email="profiles@example.test",
            full_name="Profile Owner", password="pass-word-123",
        )
        self.client.force_authenticate(self.user)

    def test_registration_does_not_require_role_or_allow_privilege_assignment(self):
        response = self.client.post("/api/auth/register/", {
            "full_name": "New User", "email": "new@example.test",
            "phone_number": "01711113333", "password": "pass-word-123","account_type": "citizen",
        }, format="json")
        self.assertEqual(response.status_code, 201)
        account = User.objects.get(email="new@example.test")
        self.assertEqual(account.role, "Citizen")
        self.assertFalse(account.is_staff)
        self.assertFalse(account.is_superuser)
        self.assertEqual(account.profiles.count(), 1)
        self.assertEqual(
            account.profiles.get().profile_type,
            UserProfile.Type.CITIZEN,
        )
        self.assertEqual(account.active_profile.profile_type, UserProfile.Type.CITIZEN)
        forbidden = self.client.post("/api/auth/register/", {
            "full_name": "Attacker", "email": "attacker@example.test",
            "phone_number": "01711114444", "password": "pass-word-123", "role": "Admin",
        }, format="json")
        self.assertEqual(forbidden.status_code, 400)

    def test_user_can_create_multiple_profiles_and_switch_without_new_account(self):
        for kind, details in (("volunteer", {}), ("farmer", {}), ("blood_donor", {"blood_group": "A+", "area": "Dhaka"})):
            response = self.client.post("/api/auth/profiles/", {"profile_type": kind, "details": details}, format="json")
            self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(UserProfile.objects.filter(user=self.user).count(), 3)
        self.assertEqual(User.objects.count(), 1)
        listed = self.client.get("/api/auth/profiles/").data
        self.assertEqual(len(listed["data"] if isinstance(listed, dict) else listed), 3)
        profile = UserProfile.objects.get(user=self.user, profile_type="farmer")
        response = self.client.put("/api/auth/active-profile/", {"profile_id": profile.id}, format="json")
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.active_profile_id, profile.id)
        self.assertEqual(self.user.role, "Farmer")

    def test_duplicate_and_foreign_profile_access_are_rejected(self):
        profile = UserProfile.objects.create(user=self.user, profile_type="citizen")
        duplicate = self.client.post("/api/auth/profiles/", {"profile_type": "citizen"}, format="json")
        self.assertEqual(duplicate.status_code, 400)
        other = User.objects.create_user(phone_number="01711115555", email="other@example.test", full_name="Other", password="pass-word-123")
        foreign = UserProfile.objects.create(user=other, profile_type="farmer")
        self.assertEqual(self.client.get(f"/api/auth/profiles/{foreign.id}/").status_code, 404)
        response = self.client.patch(f"/api/auth/profiles/{profile.id}/", {"user": str(other.user_id)}, format="json")
        self.assertEqual(response.status_code, 400)
        profile.refresh_from_db()
        self.assertEqual(profile.user_id, self.user.user_id)
        self.assertEqual(self.client.put("/api/auth/active-profile/", {"profile_id": foreign.id}, format="json").status_code, 404)
