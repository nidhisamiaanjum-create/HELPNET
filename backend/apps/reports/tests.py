from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from apps.blood.models import BloodRequest
from apps.farmer.models import ProduceListing
from apps.goods.models import GoodsListing
from apps.verification.models import AdminActionLog
from apps.volunteer.models import VolunteerOpportunity
from .models import Report

User = get_user_model()


class ReportTests(APITestCase):
    def setUp(self):
        self.citizen = User.objects.create_user(
            phone_number="01711117777",
            email="citizen_rep@example.com",
            full_name="Citizen Reporter",
            password="password123",
            role="Citizen",
        )
        self.reported = User.objects.create_user(
            phone_number="01822228888",
            email="reported_col@example.com",
            full_name="Reported User",
            password="password123",
            role="Volunteer",
        )
        self.admin = User.objects.create_user(
            phone_number="01933339999",
            email="admin@example.com",
            full_name="HELPNET Admin",
            password="password123",
            role="Admin",
        )

    def test_submit_report(self):
        self.client.force_authenticate(user=self.citizen)
        url = reverse("reports-list-create")
        payload = {
            "reported_user": str(self.reported.user_id),
            "category": "no_show",
            "description": "Collector did not arrive at the scheduled time.",
        }
        response = self.client.post(url, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["category"], "no_show")
        self.assertEqual(response.data["status"], "pending")
        self.assertEqual(Report.objects.count(), 1)

    def create_flagged(self, target):
        return Report.objects.create(
            reporter=self.citizen,
            reported_user=self.reported,
            content_object=target,
            category=Report.Category.FRAUD,
            description="Suspicious content",
        )

    def test_only_admin_can_access_moderation_actions(self):
        target = BloodRequest.objects.create(requester=self.reported, blood_group="O+", area="Dhaka")
        report = self.create_flagged(target)
        self.client.force_authenticate(user=self.citizen)
        response = self.client.post(reverse("reports-moderation"), {"report_id": str(report.pk), "action": "remove"})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        queue = self.client.get(f"{reverse('reports-moderation')}?content_type=farmer.producelisting")
        self.assertEqual(queue.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(BloodRequest.objects.filter(pk=target.pk).exists())

    def test_admin_reviews_and_removes_flagged_blood_request_with_audit_log(self):
        target = BloodRequest.objects.create(requester=self.reported, blood_group="O+", area="Dhaka")
        report = self.create_flagged(target)
        self.client.force_authenticate(user=self.admin)
        review = self.client.post(reverse("reports-moderation"), {"report_id": str(report.pk), "action": "review"})
        self.assertEqual(review.status_code, status.HTTP_200_OK)
        report.refresh_from_db()
        self.assertEqual(report.status, Report.Status.REVIEWED)
        removed = self.client.post(reverse("reports-moderation"), {"report_id": str(report.pk), "action": "remove", "reason": "Fake request"})
        self.assertEqual(removed.status_code, status.HTTP_200_OK)
        self.assertFalse(BloodRequest.objects.filter(pk=target.pk).exists())
        self.assertEqual(AdminActionLog.objects.filter(admin=self.admin, action=AdminActionLog.Action.MODERATION).count(), 2)

    def test_admin_can_edit_farmer_and_remove_goods_and_volunteer_content(self):
        produce = ProduceListing.objects.create(
            farmer=self.reported, produce_name="Potato", category="Vegetables", price=20,
            unit="kg", quantity="20 kg", location="Dhaka",
        )
        goods = GoodsListing.objects.create(
            seller=self.reported, title="Used chair", description="Description", condition="Good",
            asking_price=100, location="Dhaka",
        )
        opportunity = VolunteerOpportunity.objects.create(
            title="Clean-up", description="Community event", date="2026-10-03", location="Dhaka",
            required_volunteers=4, coordinator=self.reported,
        )
        produce_report = self.create_flagged(produce)
        goods_report = self.create_flagged(goods)
        volunteer_report = self.create_flagged(opportunity)
        self.client.force_authenticate(user=self.admin)

        edit = self.client.post(reverse("reports-moderation"), {
            "report_id": str(produce_report.pk), "action": "edit", "changes": {"description": "Updated moderation text"},
        }, format="json")
        self.assertEqual(edit.status_code, status.HTTP_200_OK)
        produce.refresh_from_db()
        self.assertEqual(produce.description, "Updated moderation text")

        for report in (goods_report, volunteer_report):
            removed = self.client.post(reverse("reports-moderation"), {"report_id": str(report.pk), "action": "remove"})
            self.assertEqual(removed.status_code, status.HTTP_200_OK)
        self.assertFalse(GoodsListing.objects.filter(pk=goods.pk).exists())
        self.assertFalse(VolunteerOpportunity.objects.filter(pk=opportunity.pk).exists())
        self.assertEqual(AdminActionLog.objects.filter(admin=self.admin, action=AdminActionLog.Action.MODERATION).count(), 3)

    def test_admin_can_moderate_unflagged_postings_from_content_queue(self):
        produce = ProduceListing.objects.create(
            farmer=self.reported, produce_name="Potato", category="Vegetables", price=20,
            unit="kg", quantity="20 kg", location="Dhaka",
        )
        self.client.force_authenticate(user=self.admin)
        queue = self.client.get(f"{reverse('reports-moderation')}?content_type=farmer.producelisting")
        self.assertEqual(queue.status_code, status.HTTP_200_OK)
        self.assertEqual(queue.data["data"][0]["id"], str(produce.pk))
        result = self.client.post(reverse("reports-moderation"), {
            "content_type": "farmer.producelisting", "object_id": str(produce.pk),
            "action": "edit", "changes": {"description": "Edited by admin"},
        }, format="json")
        self.assertEqual(result.status_code, status.HTTP_200_OK)
        produce.refresh_from_db()
        self.assertEqual(produce.description, "Edited by admin")
        self.assertTrue(AdminActionLog.objects.filter(target_reference__contains=str(produce.pk)).exists())
