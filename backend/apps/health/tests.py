from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase

from apps.ratings.models import Rating
from .models import HealthProfessional, HealthQuestion


User = get_user_model()


class HealthCommunityApiTests(APITestCase):
    def make_user(self, suffix, role="Citizen", is_verified=False):
        return User.objects.create_user(
            phone_number=f"01700000{suffix}",
            email=f"health{suffix}@example.com",
            full_name=f"Health User {suffix}",
            password="test-password-123",
            role=role,
            is_verified=is_verified,
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
        self.assertFalse(directory.data["data"][0]["is_verified"])

        administrator = self.make_user("005", role="Admin")
        self.client.force_authenticate(administrator)
        verified = self.client.patch(path, {"verification_status": "verified"}, format="json")
        self.assertEqual(verified.status_code, 200)
        self.assertTrue(verified.data["data"]["is_verified"])
