from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from .models import WastePickupRequest

User = get_user_model()


class WastePickupTests(APITestCase):
    def setUp(self):
        self.citizen = User.objects.create_user(
            phone_number="01711111111",
            email="citizen@example.com",
            full_name="Citizen User",
            password="password123",
            role="Citizen",
            location="Dhanmondi, Dhaka",
        )
        self.volunteer = User.objects.create_user(
            phone_number="01822222222",
            email="volunteer@example.com",
            full_name="Volunteer Collector",
            password="password123",
            role="Volunteer",
            location="Dhanmondi, Dhaka",
        )
        self.other_user = User.objects.create_user(
            phone_number="01933333333",
            email="other@example.com",
            full_name="Other Citizen",
            password="password123",
            role="Citizen",
            location="Gulshan, Dhaka",
        )

    def test_unauthenticated_cannot_create_request(self):
        url = reverse("waste-requests-list-create")
        response = self.client.post(url, {
            "waste_type": "Organic",
            "area": "Dhanmondi",
            "location": "Road 27",
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_citizen_can_create_and_view_request(self):
        self.client.force_authenticate(user=self.citizen)
        url = reverse("waste-requests-list-create")

        payload = {
            "waste_type": "Organic",
            "area": "Dhanmondi",
            "location": "House 12, Road 4",
            "preferred_pickup_time": "10:00 AM",
            "notes": "Large box of organic waste",
        }
        response = self.client.post(url, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["waste_type"], "Organic")
        self.assertEqual(response.data["status"], "Requested")

        # Citizen views their requests
        list_response = self.client.get(url)
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(list_response.data), 1)

    def test_citizen_only_sees_own_requests(self):
        req1 = WastePickupRequest.objects.create(
            requester=self.citizen,
            waste_type="Organic",
            area="Dhanmondi",
            location="House 1",
        )
        req2 = WastePickupRequest.objects.create(
            requester=self.other_user,
            waste_type="Recyclable",
            area="Gulshan",
            location="House 2",
        )

        self.client.force_authenticate(user=self.citizen)
        url = reverse("waste-requests-list-create")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], str(req1.id))

    def test_update_request_status(self):
        req = WastePickupRequest.objects.create(
            requester=self.citizen,
            waste_type="Organic",
            area="Dhanmondi",
            location="House 1",
        )
        self.client.force_authenticate(user=self.citizen)
        detail_url = reverse("waste-request-detail", kwargs={"id": req.id})

        response = self.client.patch(detail_url, {"status": "Contacted"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        req.refresh_from_db()
        self.assertEqual(req.status, "Contacted")

    def test_area_matching_collectors(self):
        self.client.force_authenticate(user=self.citizen)
        url = reverse("waste-available-collectors") + "?area=Dhanmondi"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        # Should include volunteer who is in Dhanmondi
        collector_names = [c["full_name"] for c in response.data["data"]]
        self.assertIn("Volunteer Collector", collector_names)


class EndToEndStoryTests(APITestCase):
    def setUp(self):
        self.citizen = User.objects.create_user(
            phone_number="01799991111",
            email="e2e_citizen@example.com",
            full_name="Citizen E2E",
            password="password123",
            role="Citizen",
            location="Mirpur, Dhaka",
        )
        self.collector = User.objects.create_user(
            phone_number="01799992222",
            email="e2e_collector@example.com",
            full_name="Collector Mirpur",
            password="password123",
            role="Volunteer",
            location="Mirpur, Dhaka",
        )
        self.farmer = User.objects.create_user(
            phone_number="01799993333",
            email="e2e_farmer@example.com",
            full_name="Farmer Jamir",
            password="password123",
            role="Farmer",
            location="Savar, Dhaka",
        )

    def test_complete_story_verification(self):
        # 1. Citizen creates waste pickup request
        self.client.force_authenticate(user=self.citizen)
        req_res = self.client.post(reverse("waste-requests-list-create"), {
            "waste_type": "Recyclable",
            "area": "Mirpur",
            "location": "Section 10, Block C",
            "preferred_pickup_time": "3:00 PM",
        })
        self.assertEqual(req_res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(req_res.data["status"], "Requested")

        # 2. Collector contact appears for matching area
        col_res = self.client.get(reverse("waste-available-collectors") + "?area=Mirpur")
        self.assertEqual(col_res.status_code, status.HTTP_200_OK)
        collector_ids = [c["user_id"] for c in col_res.data["data"]]
        self.assertIn(str(self.collector.user_id), collector_ids)

        # 3. Citizen rates & reports collector
        rate_res = self.client.post(reverse("ratings-list-create"), {
            "rated_user": str(self.collector.user_id),
            "score": 5,
            "comment": "Super clean and punctual!",
        })
        self.assertEqual(rate_res.status_code, status.HTTP_201_CREATED)

        rep_res = self.client.post(reverse("reports-list-create"), {
            "reported_user": str(self.collector.user_id),
            "category": "no_show",
            "description": "Minor delay test report",
        })
        self.assertEqual(rep_res.status_code, status.HTTP_201_CREATED)

        # 4. Farmer creates produce listing
        self.client.force_authenticate(user=self.farmer)
        prod_res = self.client.post(reverse("farmer-produce-list-create"), {
            "produce_name": "Fresh Mustard Oil",
            "category": "Other",
            "price": "220.00",
            "unit": "liter",
            "quantity": "50 liters",
            "location": "Savar, Dhaka",
            "description": "100% pure cold-pressed mustard oil.",
            "availability": "Available",
        })
        self.assertEqual(prod_res.status_code, status.HTTP_201_CREATED)
        produce_id = prod_res.data["id"]

        # 5 & 6. Consumer sees listing/details and farmer contact
        self.client.force_authenticate(user=self.citizen)
        detail_res = self.client.get(reverse("farmer-produce-detail", kwargs={"id": produce_id}))
        self.assertEqual(detail_res.status_code, status.HTTP_200_OK)
        self.assertEqual(detail_res.data["produce_name"], "Fresh Mustard Oil")
        self.assertEqual(detail_res.data["farmer_phone"], "01799993333")
        self.assertEqual(detail_res.data["farmer_name"], "Farmer Jamir")

        # 7. Farmer can change listing status
        self.client.force_authenticate(user=self.farmer)
        patch_res = self.client.patch(reverse("farmer-produce-detail", kwargs={"id": produce_id}), {
            "availability": "Unavailable"
        })
        self.assertEqual(patch_res.status_code, status.HTTP_200_OK)
        self.assertEqual(patch_res.data["availability"], "Unavailable")

        # 8. Unauthorized user cannot perform protected actions
        self.client.logout()
        unauth_res = self.client.post(reverse("farmer-produce-list-create"), {
            "produce_name": "Unauthorized Produce",
        })
        self.assertEqual(unauth_res.status_code, status.HTTP_401_UNAUTHORIZED)

        # 9. Existing auth / login works
        login_res = self.client.post("/api/auth/login/", {
            "identifier": "01799993333",
            "password": "password123",
        })
        self.assertEqual(login_res.status_code, status.HTTP_200_OK)
        self.assertIn("access", login_res.data["data"])

