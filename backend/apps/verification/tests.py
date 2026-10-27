from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework.test import APITestCase

from .models import VerificationRequest

User = get_user_model()


class PrivateVerificationDocumentTests(APITestCase):
    def setUp(self):
        self.citizen = User.objects.create_user(
            phone_number="01710001001", email="nid-citizen@example.test",
            full_name="NID Citizen", password="test-password-123", role="Citizen",
        )
        self.admin = User.objects.create_user(
            phone_number="01710001002", email="nid-admin@example.test",
            full_name="NID Admin", password="test-password-123", role="Admin",
            is_staff=True,
            is_superuser=True,
        )

    def test_nid_documents_are_private_and_admin_download_is_authorized(self):
        self.client.force_authenticate(self.citizen)
        upload = SimpleUploadedFile("identity.pdf", b"%PDF-1.7\nidentity", content_type="application/pdf")
        submitted = self.client.post(reverse("verification-submit"), {
            "document_type": "nid",
            "document": upload,
        }, format="multipart")
        self.assertEqual(submitted.status_code, 201, submitted.data)
        verification = VerificationRequest.objects.get(user=self.citizen)
        self.addCleanup(verification.document.delete, save=False)

        admin_list = self.client.get(reverse("admin-verification-list"))
        self.assertEqual(admin_list.status_code, 403)
        self.assertEqual(self.client.get(reverse("admin-verification-document", args=[verification.pk])).status_code, 403)

        self.client.force_authenticate(self.admin)
        admin_list = self.client.get(reverse("admin-verification-list"))
        self.assertEqual(admin_list.status_code, 200)
        document_url = admin_list.data["data"][0]["document_url"]
        self.assertEqual(document_url, reverse("admin-verification-document", args=[verification.pk]))
        downloaded = self.client.get(document_url)
        self.assertEqual(downloaded.status_code, 200)
        self.assertEqual(b"".join(downloaded.streaming_content), b"%PDF-1.7\nidentity")
        with self.assertRaises(ValueError):
            verification.document.url
