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

    def test_user_can_create_and_select_pending_ngo_profile_without_nid_approval(self):
        response = self.client.post(
            "/api/auth/profiles/",
            {"profile_type": "ngo", "display_name": "Community NGO"},
            format="json",
        )
        self.assertEqual(response.status_code, 201, response.data)
        profile = UserProfile.objects.get(user=self.user, profile_type="ngo")
        self.assertEqual(
            profile.ngo_approval_status,
            UserProfile.NGOApprovalStatus.PENDING,
        )
        self.assertFalse(self.user.is_verified)
        selected = self.client.put(
            "/api/auth/active-profile/",
            {"profile_id": profile.id},
            format="json",
        )
        self.assertEqual(selected.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.role, "NGO")
        self.assertFalse(self.user.is_verified)

    def test_ngo_account_can_create_personal_profiles_and_switch_between_them(self):
        ngo_response = self.client.post(
            "/api/auth/profiles/",
            {"profile_type": "ngo", "display_name": "Community NGO"},
            format="json",
        )
        self.assertEqual(ngo_response.status_code, 201, ngo_response.data)
        ngo_profile_id = ngo_response.data["data"]["id"]

        volunteer_response = self.client.post(
            "/api/auth/profiles/",
            {"profile_type": "volunteer"},
            format="json",
        )
        farmer_response = self.client.post(
            "/api/auth/profiles/",
            {"profile_type": "farmer"},
            format="json",
        )
        donor_response = self.client.post(
            "/api/auth/profiles/",
            {
                "profile_type": "blood_donor",
                "details": {"blood_group": "A+", "area": "Dhaka"},
            },
            format="json",
        )
        citizen_response = self.client.post(
            "/api/auth/profiles/",
            {"profile_type": "citizen"},
            format="json",
        )
        self.assertEqual(volunteer_response.status_code, 201)
        self.assertEqual(farmer_response.status_code, 201)
        self.assertEqual(donor_response.status_code, 201)
        self.assertEqual(citizen_response.status_code, 201)
        self.assertEqual(User.objects.count(), 1)

        for profile in (
            volunteer_response.data["data"],
            farmer_response.data["data"],
            donor_response.data["data"],
            citizen_response.data["data"],
        ):
            selected = self.client.put(
                "/api/auth/active-profile/",
                {"profile_id": profile["id"]},
                format="json",
            )
            self.assertEqual(selected.status_code, 200)
            self.user.refresh_from_db()
            self.assertEqual(self.user.active_profile_id, profile["id"])
            self.assertFalse(self.user.is_verified)

        selected_ngo = self.client.put(
            "/api/auth/active-profile/",
            {"profile_id": ngo_profile_id},
            format="json",
        )
        self.assertEqual(selected_ngo.status_code, 200)
        self.assertEqual(self.user.profiles.count(), 5)

    def test_active_profile_deactivation_clears_legacy_role_and_can_be_reactivated(self):
        profile = UserProfile.objects.create(
            user=self.user,
            profile_type=UserProfile.Type.FARMER,
        )
        self.user.active_profile = profile
        self.user.role = "Farmer"
        self.user.save(update_fields=["active_profile", "role"])

        deleted = self.client.delete(f"/api/auth/profiles/{profile.id}/")
        self.assertEqual(deleted.status_code, 204)
        profile.refresh_from_db()
        self.user.refresh_from_db()
        self.assertEqual(profile.status, UserProfile.Status.INACTIVE)
        self.assertIsNone(self.user.active_profile_id)
        self.assertEqual(self.user.role, "")
        self.assertEqual(User.objects.count(), 1)
        listed = self.client.get("/api/auth/profiles/")
        self.assertEqual(listed.status_code, 200)
        inactive_profile = next(
            item
            for item in listed.data["data"]
            if item["id"] == profile.id
        )
        self.assertEqual(inactive_profile["status"], "inactive")

        reactivated = self.client.post(
            f"/api/auth/profiles/{profile.id}/reactivate/",
            format="json",
        )
        self.assertEqual(reactivated.status_code, 200)
        profile.refresh_from_db()
        self.assertEqual(profile.status, UserProfile.Status.ACTIVE)

        selected = self.client.put(
            "/api/auth/active-profile/",
            {"profile_id": profile.id},
            format="json",
        )
        self.assertEqual(selected.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.active_profile_id, profile.id)
        self.assertEqual(self.user.role, "Farmer")

    def test_user_cannot_reactivate_another_users_profile(self):
        other = User.objects.create_user(
            phone_number="01711115556",
            email="inactive-owner@example.test",
            full_name="Other Owner",
            password="test-pass-123",
        )
        profile = UserProfile.objects.create(
            user=other,
            profile_type=UserProfile.Type.FARMER,
            status=UserProfile.Status.INACTIVE,
        )
        response = self.client.post(
            f"/api/auth/profiles/{profile.id}/reactivate/",
            format="json",
        )
        self.assertEqual(response.status_code, 404)
        profile.refresh_from_db()
        self.assertEqual(profile.status, UserProfile.Status.INACTIVE)

    def test_role_profile_edits_validate_and_save_existing_role_fields(self):
        created_volunteer = self.client.post(
            "/api/auth/profiles/",
            {"profile_type": "volunteer"},
            format="json",
        )
        self.assertEqual(created_volunteer.status_code, 201)
        volunteer_id = created_volunteer.data["data"]["id"]
        response = self.client.patch(
            f"/api/auth/profiles/{volunteer_id}/",
            {
                "display_name": "Community Volunteer",
                "details": {
                    "skills": "First aid, translation",
                    "availability": "Weekends",
                    "location": "Dhaka",
                    "blood_group": "A+",
                    "supporting_certificates": "First aid certificate",
                },
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(
            response.data["details"]["skills"],
            "First aid, translation",
        )
        self.assertEqual(response.data["display_name"], "Community Volunteer")

        created_donor = self.client.post(
            "/api/auth/profiles/",
            {
                "profile_type": "blood_donor",
                "details": {"blood_group": "A+", "area": "Dhaka"},
            },
            format="json",
        )
        self.assertEqual(created_donor.status_code, 201)
        donor_id = created_donor.data["data"]["id"]
        invalid = self.client.patch(
            f"/api/auth/profiles/{donor_id}/",
            {
                "display_name": "Donor profile",
                "details": {"blood_group": "INVALID"},
            },
            format="json",
        )
        self.assertEqual(invalid.status_code, 400)
        donor = UserProfile.objects.get(id=donor_id)
        self.assertEqual(donor.display_name, "")

        updated = self.client.patch(
            f"/api/auth/profiles/{donor_id}/",
            {
                "display_name": "Donor profile",
                "details": {
                    "blood_group": "O+",
                    "area": "Chattogram",
                    "availability": "busy",
                },
            },
            format="json",
        )
        self.assertEqual(updated.status_code, 200, updated.data)
        self.assertEqual(updated.data["details"]["blood_group"], "O+")
        self.assertEqual(updated.data["details"]["area"], "Chattogram")

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
