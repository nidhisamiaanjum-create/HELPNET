from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from rest_framework.test import APIClient

from .models import GoodsInterest, GoodsListing, GoodsReport


User = get_user_model()


class GoodsExchangeTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            phone_number="01000000011",
            email="goods-owner@example.test",
            full_name="Goods Owner",
            password="test-password-123",
        )
        self.other = User.objects.create_user(
            phone_number="01000000012",
            email="goods-interested@example.test",
            full_name="Interested User",
            password="test-password-123",
        )
        self.listing = GoodsListing.objects.create(
            seller=self.owner,
            title="Used desk",
            description="Wooden desk in good condition.",
            condition=GoodsListing.Condition.GOOD,
            asking_price="1500.00",
            location="Dhaka",
        )
        self.api = APIClient()

    def test_user_creates_listing_and_listing_appears_in_list_and_details(self):
        self.api.force_authenticate(self.owner)
        created = self.api.post("/api/goods/listings/", {
            "title": "Used chair",
            "description": "A sturdy chair.",
            "condition": "Like new",
            "asking_price": "700.00",
            "location": "Chattogram",
        }, format="json")
        self.assertEqual(created.status_code, 201)
        listing_id = created.data["data"]["id"]

        listing_list = self.api.get("/api/goods/listings/")
        self.assertEqual(listing_list.status_code, 200)
        self.assertIn(listing_id, [item["id"] for item in listing_list.data["data"]])

        detail = self.api.get(f"/api/goods/listings/{listing_id}/")
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(detail.data["data"]["title"], "Used chair")
        self.assertTrue(detail.data["data"]["is_owner"])
        self.assertEqual(detail.data["data"]["seller_contact"]["phone_number"], self.owner.phone_number)

        self.api.force_authenticate(self.other)
        public_detail = self.api.get(f"/api/goods/listings/{listing_id}/")
        self.assertFalse(public_detail.data["data"]["is_owner"])
        # Existing privacy preferences control which seller contacts are public.
        self.assertNotIn("phone_number", public_detail.data["data"]["seller_contact"])
        self.assertNotIn("email", public_detail.data["data"]["seller_contact"])

    def test_interest_is_created_once_per_user_and_listing(self):
        self.api.force_authenticate(self.other)
        url = f"/api/goods/listings/{self.listing.pk}/interest/"
        first = self.api.post(url, {}, format="json")
        duplicate = self.api.post(url, {}, format="json")
        self.assertEqual(first.status_code, 201)
        self.assertEqual(duplicate.status_code, 400)
        self.assertEqual(GoodsInterest.objects.filter(listing=self.listing, interested_user=self.other).count(), 1)

    def test_only_owner_can_change_listing_status(self):
        self.api.force_authenticate(self.other)
        denied = self.api.patch(f"/api/goods/listings/{self.listing.pk}/status/", {"status": "Reserved"}, format="json")
        self.assertEqual(denied.status_code, 403)

        self.api.force_authenticate(self.owner)
        updated = self.api.patch(f"/api/goods/listings/{self.listing.pk}/status/", {"status": "Reserved"}, format="json")
        self.assertEqual(updated.status_code, 200)
        self.assertEqual(updated.data["data"]["status"], GoodsListing.Status.RESERVED)
        self.assertNotIn(self.listing.pk, [item["id"] for item in self.api.get("/api/goods/listings/").data["data"]])

    def test_report_and_unauthenticated_protected_actions_and_disclaimer(self):
        self.api.force_authenticate(self.other)
        reported = self.api.post(f"/api/goods/listings/{self.listing.pk}/reports/", {
            "reason": "Misleading description",
            "description": "The listed condition does not match the details.",
        }, format="json")
        self.assertEqual(reported.status_code, 201)
        self.assertEqual(GoodsReport.objects.count(), 1)

        guest = APIClient()
        self.assertEqual(guest.get("/api/goods/listings/").status_code, 401)
        self.assertEqual(guest.post("/api/goods/listings/", {"title": "Guest"}, format="json").status_code, 401)
        self.assertEqual(guest.post(f"/api/goods/listings/{self.listing.pk}/interest/", {}, format="json").status_code, 401)
        self.assertEqual(guest.patch(f"/api/goods/listings/{self.listing.pk}/status/", {"status": "Removed"}, format="json").status_code, 401)
        self.assertEqual(guest.post(f"/api/goods/listings/{self.listing.pk}/reports/", {"reason": "Test"}, format="json").status_code, 401)

    @override_settings(ALLOWED_HOSTS=["testserver"])
    def test_goods_pages_load_and_disclaimer_is_present(self):
        client = Client()
        self.assertEqual(client.get("/goods-list/").status_code, 200)
        self.assertEqual(client.get("/create-goods/").status_code, 200)
        details = client.get("/goods-details/?listing_id=1")
        self.assertEqual(details.status_code, 200)
        self.assertContains(details, "HELPNET does not handle payments and does not guarantee item condition. Exchanges are arranged directly between users.")
