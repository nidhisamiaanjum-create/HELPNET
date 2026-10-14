from io import BytesIO
from tempfile import TemporaryDirectory

from PIL import Image
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from rest_framework.test import APIClient

from apps.reports.models import Report
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

    def test_listing_image_is_validated_and_persisted(self):
        self.api.force_authenticate(self.owner)
        image_bytes = BytesIO()
        Image.new("RGB", (2, 2), color="teal").save(image_bytes, format="PNG")
        valid_image = SimpleUploadedFile(
            "item.png", image_bytes.getvalue(), content_type="image/png"
        )

        with TemporaryDirectory() as media_root, override_settings(MEDIA_ROOT=media_root):
            created = self.api.post("/api/goods/listings/", {
                "title": "Chair with photo",
                "description": "A chair.",
                "condition": "Good",
                "asking_price": "50.00",
                "location": "Dhaka",
                "image": valid_image,
            }, format="multipart")
            self.assertEqual(created.status_code, 201, created.data)
            listing = GoodsListing.objects.get(pk=created.data["data"]["id"])
            self.assertTrue(listing.image)
            self.assertTrue(listing.image.storage.exists(listing.image.name))

            invalid_image = SimpleUploadedFile(
                "fake.png", b"not an image", content_type="image/png"
            )
            rejected = self.api.post("/api/goods/listings/", {
                "title": "Invalid photo",
                "description": "A chair.",
                "condition": "Good",
                "asking_price": "50.00",
                "location": "Dhaka",
                "image": invalid_image,
            }, format="multipart")
            self.assertEqual(rejected.status_code, 400)
            self.assertIn("image", rejected.data["message"])

            oversized_image = SimpleUploadedFile(
                "large.png", b"x" * (5 * 1024 * 1024 + 1),
                content_type="image/png",
            )
            oversized = self.api.post("/api/goods/listings/", {
                "title": "Oversized photo",
                "description": "A chair.",
                "condition": "Good",
                "asking_price": "50.00",
                "location": "Dhaka",
                "image": oversized_image,
            }, format="multipart")
            self.assertEqual(oversized.status_code, 400)
            self.assertIn("image", oversized.data["message"])

    def test_interest_is_created_once_per_user_and_listing(self):
        self.api.force_authenticate(self.other)
        url = f"/api/goods/listings/{self.listing.pk}/interest/"
        first = self.api.post(url, {}, format="json")
        duplicate = self.api.post(url, {}, format="json")
        self.assertEqual(first.status_code, 201)
        self.assertEqual(duplicate.status_code, 400)
        self.assertEqual(GoodsInterest.objects.filter(listing=self.listing, interested_user=self.other).count(), 1)

    def test_interest_reveals_contact_details_only_after_interest_is_confirmed(self):
        self.api.force_authenticate(self.other)
        detail_before = self.api.get(f"/api/goods/listings/{self.listing.pk}/")
        self.assertNotIn("phone_number", detail_before.data["data"]["seller_contact"])
        self.assertNotIn("email", detail_before.data["data"]["seller_contact"])

        interest = self.api.post(f"/api/goods/listings/{self.listing.pk}/interest/", {}, format="json")
        self.assertEqual(interest.status_code, 201)

        detail_after = self.api.get(f"/api/goods/listings/{self.listing.pk}/")
        self.assertEqual(detail_after.data["data"]["seller_contact"]["phone_number"], self.owner.phone_number)
        self.assertEqual(detail_after.data["data"]["seller_contact"]["email"], self.owner.email)

    def test_only_owner_can_change_listing_status(self):
        self.api.force_authenticate(self.other)
        denied = self.api.patch(f"/api/goods/listings/{self.listing.pk}/status/", {"status": "Reserved"}, format="json")
        self.assertEqual(denied.status_code, 403)

        self.api.force_authenticate(self.owner)
        updated = self.api.patch(f"/api/goods/listings/{self.listing.pk}/status/", {"status": "Reserved"}, format="json")
        self.assertEqual(updated.status_code, 200)
        self.assertEqual(updated.data["data"]["status"], GoodsListing.Status.RESERVED)
        self.assertNotIn(self.listing.pk, [item["id"] for item in self.api.get("/api/goods/listings/").data["data"]])

        reopened = self.api.patch(f"/api/goods/listings/{self.listing.pk}/status/", {"status": "Available"}, format="json")
        self.assertEqual(reopened.status_code, 200)

        invalid = self.api.patch(f"/api/goods/listings/{self.listing.pk}/status/", {"status": "Exchanged"}, format="json")
        self.assertEqual(invalid.status_code, 400)
        self.assertEqual(invalid.data["message"], "Status cannot change from Available to Exchanged.")

    def test_report_and_unauthenticated_protected_actions_and_disclaimer(self):
        self.api.force_authenticate(self.other)
        reported = self.api.post(f"/api/goods/listings/{self.listing.pk}/reports/", {
            "reason": "Misleading description",
            "description": "The listed condition does not match the details.",
        }, format="json")
        self.assertEqual(reported.status_code, 201)
        shared_report = Report.objects.get(content_type__app_label="goods", object_id=str(self.listing.pk))
        self.assertEqual(shared_report.reporter, self.other)
        self.assertEqual(shared_report.reported_user, self.owner)
        self.assertEqual(shared_report.content_object, self.listing)

        admin = User.objects.create_user(
            phone_number="01000000013",
            email="goods-admin@example.test",
            full_name="Goods Admin",
            password="test-password-123",
            role="Admin",
        )
        self.api.force_authenticate(admin)
        queue = self.api.get("/api/reports/")
        self.assertEqual(queue.status_code, 200)
        self.assertIn(str(shared_report.pk), [str(item["id"]) for item in queue.data])
        moderated = self.api.post("/api/reports/moderation/", {
            "report_id": str(shared_report.pk),
            "action": "review",
        }, format="json")
        self.assertEqual(moderated.status_code, 200)
        shared_report.refresh_from_db()
        self.assertEqual(shared_report.status, Report.Status.REVIEWED)

        guest = APIClient()
        self.assertEqual(guest.get("/api/goods/listings/").status_code, 401)
        self.assertEqual(guest.get(f"/api/goods/listings/{self.listing.pk}/").status_code, 401)
        self.assertEqual(guest.post("/api/goods/listings/", {"title": "Guest"}, format="json").status_code, 401)
        self.assertEqual(guest.post(f"/api/goods/listings/{self.listing.pk}/interest/", {}, format="json").status_code, 401)
        self.assertEqual(guest.patch(f"/api/goods/listings/{self.listing.pk}/status/", {"status": "Removed"}, format="json").status_code, 401)
        self.assertEqual(guest.post(f"/api/goods/listings/{self.listing.pk}/reports/", {"reason": "Test"}, format="json").status_code, 401)

    @override_settings(ALLOWED_HOSTS=["testserver"])
    def test_goods_pages_load_and_disclaimer_is_present(self):
        client = Client()
        self.assertEqual(client.get("/goods-list/").status_code, 200)
        create_page = client.get("/create-goods/")
        self.assertEqual(create_page.status_code, 200)
        self.assertContains(create_page, 'enctype="multipart/form-data"')
        self.assertContains(create_page, 'accept="image/jpeg,image/png,image/webp"')
        details = client.get("/goods-details/?listing_id=1")
        self.assertEqual(details.status_code, 200)
        for value in ("Available", "Reserved", "Exchanged", "Removed"):
            self.assertContains(details, f'value="{value}"')
        self.assertContains(details, "HELPNET does not handle payments and does not guarantee item condition. Exchanges are arranged directly between users.")
