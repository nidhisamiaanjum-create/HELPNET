from django.test import TestCase
from rest_framework import status
from rest_framework.test import APITestCase


class AuthPermissionTests(APITestCase):

    def test_register_is_public(self):
        response = self.client.post(
            "/api/auth/register/",
            {
                "full_name": "ST09 Test User",
                "email": "permissiontest@example.com",
                "phone_number": "01800000001",
                "password": "TestPassword123",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_login_is_public(self):
        response = self.client.post(
            "/api/auth/login/",
            {
                "identifier": "nonexistent@example.com",
                "password": "WrongPassword123",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout_requires_authentication(self):
        response = self.client.post(
            "/api/auth/logout/",
            {
                "refresh": "invalid-refresh-token",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_password_reset_is_public(self):
        response = self.client.post(
            "/api/auth/password-reset/",
            {
                "email": "nonexistent@example.com",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_password_reset_confirm_is_public(self):
        response = self.client.post(
            "/api/auth/password-reset-confirm/",
            {
                "uid": "invalid",
                "token": "invalid",
                "new_password": "NewPassword123",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)