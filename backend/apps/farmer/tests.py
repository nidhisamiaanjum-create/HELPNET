from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from .models import ProduceListing

User = get_user_model()


class FarmerMarketTests(APITestCase):
    def setUp(self):
        self.farmer = User.objects.create_user(
            phone_number="01711112222",
            email="farmer@example.com",
            full_name="Farmer Karim",
            password="password123",
            role="Farmer",
            location="Savar, Dhaka",
        )
        self.consumer = User.objects.create_user(
            phone_number="01833334444",
            email="consumer@example.com",
            full_name="Consumer Rahim",
            password="password123",
            role="Citizen",
            location="Mirpur, Dhaka",
        )
        self.other_farmer = User.objects.create_user(
            phone_number="01955556666",
            email="otherfarmer@example.com",
            full_name="Farmer Jamila",
            password="password123",
            role="Farmer",
            location="Bogura",
        )

    def test_farmer_can_create_produce(self):
        self.client.force_authenticate(user=self.farmer)
        url = reverse("farmer-produce-list-create")
        payload = {
            "produce_name": "Fresh Organic Tomatoes",
            "category": "Vegetables",
            "price": "45.00",
            "unit": "kg",
            "quantity": "200 kg",
            "location": "Savar, Dhaka",
            "description": "Chemical-free harvest.",
            "availability": "Available",
        }
        response = self.client.post(url, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["produce_name"], "Fresh Organic Tomatoes")
        self.assertEqual(response.data["farmer_name"], "Farmer Karim")

    def test_consumer_can_view_produce_and_farmer_contact(self):
        produce = ProduceListing.objects.create(
            farmer=self.farmer,
            produce_name="Sweet Potatoes",
            category="Vegetables",
            price=30.00,
            unit="kg",
            quantity="50 kg",
            location="Savar, Dhaka",
            description="Freshly harvested sweet potatoes.",
            availability="Available",
        )
        self.client.force_authenticate(user=self.consumer)
        detail_url = reverse("farmer-produce-detail", kwargs={"id": produce.id})
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["produce_name"], "Sweet Potatoes")
        self.assertEqual(response.data["farmer_name"], "Farmer Karim")
        self.assertEqual(response.data["farmer_phone"], "01711112222")

    def test_farmer_can_update_and_delete_own_produce(self):
        produce = ProduceListing.objects.create(
            farmer=self.farmer,
            produce_name="Green Chili",
            category="Spices",
            price=80.00,
            unit="kg",
            quantity="30 kg",
            location="Savar, Dhaka",
            availability="Available",
        )
        self.client.force_authenticate(user=self.farmer)
        detail_url = reverse("farmer-produce-detail", kwargs={"id": produce.id})

        # Update status
        patch_res = self.client.patch(detail_url, {"availability": "Unavailable", "price": "75.00"})
        self.assertEqual(patch_res.status_code, status.HTTP_200_OK)
        produce.refresh_from_db()
        self.assertEqual(produce.availability, "Unavailable")
        self.assertEqual(float(produce.price), 75.00)

        # Delete
        del_res = self.client.delete(detail_url)
        self.assertEqual(del_res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(ProduceListing.objects.filter(id=produce.id).exists())

    def test_other_user_cannot_edit_or_delete_produce(self):
        produce = ProduceListing.objects.create(
            farmer=self.farmer,
            produce_name="Cabbage",
            category="Vegetables",
            price=25.00,
            unit="piece",
            quantity="100 pcs",
            location="Savar, Dhaka",
            availability="Available",
        )
        self.client.force_authenticate(user=self.other_farmer)
        detail_url = reverse("farmer-produce-detail", kwargs={"id": produce.id})

        patch_res = self.client.patch(detail_url, {"price": "10.00"})
        self.assertEqual(patch_res.status_code, status.HTTP_403_FORBIDDEN)

        del_res = self.client.delete(detail_url)
        self.assertEqual(del_res.status_code, status.HTTP_403_FORBIDDEN)

    def test_price_range_uses_only_other_farmers_active_listings_in_same_category_and_area(self):
        current = ProduceListing.objects.create(
            farmer=self.farmer, produce_name="Tomato", category="Vegetables", price=45,
            unit="kg", quantity="10 kg", location="Savar, Dhaka",
        )
        ProduceListing.objects.create(
            farmer=self.farmer, produce_name="Tomato", category="Vegetables", price=90,
            unit="kg", quantity="5 kg", location="Savar, Dhaka",
        )
        ProduceListing.objects.create(
            farmer=self.other_farmer, produce_name="Tomato", category="Vegetables", price=55,
            unit="kg", quantity="5 kg", location="Savar, Dhaka",
        )
        ProduceListing.objects.create(
            farmer=self.other_farmer, produce_name="Tomato", category="Vegetables", price=75,
            unit="kg", quantity="5 kg", location="Bogura",
        )
        unavailable = ProduceListing.objects.create(
            farmer=self.other_farmer, produce_name="Tomato", category="Vegetables", price=10,
            unit="kg", quantity="5 kg", location="Savar, Dhaka", availability="Unavailable",
        )
        self.client.force_authenticate(user=self.farmer)
        response = self.client.get(reverse("farmer-produce-price-range", kwargs={"id": current.id}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["count"], 1)
        self.assertEqual(float(response.data["data"]["minimum"]), 55.0)
        self.assertEqual(float(response.data["data"]["maximum"]), 55.0)
        self.assertNotEqual(unavailable.price, response.data["data"]["minimum"])

    def test_user_can_report_a_farmer_listing(self):
        from apps.reports.models import Report

        listing = ProduceListing.objects.create(
            farmer=self.farmer, produce_name="Tomato", category="Vegetables", price=45,
            unit="kg", quantity="10 kg", location="Savar, Dhaka",
        )
        self.client.force_authenticate(user=self.consumer)
        response = self.client.post(
            reverse("farmer-produce-report", kwargs={"id": listing.id}),
            {"description": "This listing appears suspicious."},
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        report = Report.objects.get(pk=response.data["data"]["id"])
        self.assertEqual(report.reporter, self.consumer)
        self.assertEqual(report.content_object, listing)
