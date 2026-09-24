from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model


User = get_user_model()


class AuthPermissionTests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            phone_number="01710000001",
            email="permissiontest@example.com",
            full_name="Permission Test User",
            password="TestPassword123",
        )

    def get_access_token(self):
        refresh = RefreshToken.for_user(self.user)
        return str(refresh.access_token)

    def test_register_is_public(self):
        response = self.client.post(
            "/api/auth/register/",
            {
                "full_name": "New Test User",
                "email": "newpermission@example.com",
                "phone_number": "01710000002",
                "password": "TestPassword123",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

    def test_login_is_public(self):
        response = self.client.post(
            "/api/auth/login/",
            {
                "identifier": "nonexistent@example.com",
                "password": "WrongPassword123",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_me_requires_authentication(self):
        response = self.client.get("/api/auth/me/")

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_me_accepts_valid_jwt(self):
        token = self.get_access_token()

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {token}"
        )

        response = self.client.get("/api/auth/me/")

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

    def test_me_rejects_invalid_jwt(self):
        self.client.credentials(
            HTTP_AUTHORIZATION="Bearer invalid-token"
        )

        response = self.client.get("/api/auth/me/")

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_logout_requires_authentication(self):
        self.client.credentials()

        response = self.client.post(
            "/api/auth/logout/",
            {
                "refresh": "invalid-refresh-token",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_logout_accepts_authenticated_request(self):
        token = self.get_access_token()

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {token}"
        )

        response = self.client.post(
            "/api/auth/logout/",
            {
                "refresh": "invalid-refresh-token",
            },
            format="json",
        )

        # Authentication passed; the refresh token itself is invalid.
        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_password_reset_is_public(self):
        response = self.client.post(
            "/api/auth/password-reset/",
            {
                "email": "nonexistent@example.com",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

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

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )