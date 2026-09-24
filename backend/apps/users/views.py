from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
# at the top, with other imports:
from .serializers import (
    RegisterSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
    UserProfileSerializer,
    PublicUserProfileSerializer,
)


User = get_user_model()


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.save()

            return Response(
                {
                    "success": True,
                    "data": {
                        "user_id": str(user.user_id),
                        "full_name": user.full_name,
                        "email": user.email,
                        "phone_number": user.phone_number,
                        "role": user.role,
                    },
                    "message": "Registration successful."
                },
                status=status.HTTP_201_CREATED
            )

        return Response(
            {
                "success": False,
                "data": None,
                "message": serializer.errors
            },
            status=status.HTTP_400_BAD_REQUEST
        )


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):

        identifier = request.data.get("identifier")
        password = request.data.get("password")

        if not identifier or not password:
            return Response(
                {
                    "success": False,
                    "data": None,
                    "message": "Email or phone number and password are required."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        identifier = identifier.strip()

        try:
            if "@" in identifier:
                user = User.objects.get(email=identifier)
            else:
                user = User.objects.get(phone_number=identifier)
        except User.DoesNotExist:
            user = None

        if user is None or not user.check_password(password):
            return Response(
                {
                    "success": False,
                    "data": None,
                    "message": "Invalid email/phone number or password."
                },
                status=status.HTTP_401_UNAUTHORIZED
            )

        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "success": True,
                "data": {
                    "user_id": str(user.user_id),
                    "full_name": user.full_name,
                    "email": user.email,
                    "phone_number": user.phone_number,
                    "role": user.role,
                    "access": str(refresh.access_token),
                    "refresh": str(refresh),
                },
                "message": "Login successful."
            },
            status=status.HTTP_200_OK
        )


class LogoutView(APIView):
    def post(self, request):
        refresh_token = request.data.get("refresh")

        if not refresh_token:
            return Response(
                {
                    "success": False,
                    "data": None,
                    "message": "Refresh token is required."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()

            return Response(
                {
                    "success": True,
                    "data": None,
                    "message": "Logout successful."
                },
                status=status.HTTP_200_OK
            )

        except Exception:
            return Response(
                {
                    "success": False,
                    "data": None,
                    "message": "Invalid or expired refresh token."
                },
                status=status.HTTP_400_BAD_REQUEST
            )
class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                {
                    "success": False,
                    "data": None,
                    "message": serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        email = serializer.validated_data["email"]

        try:
            user = User.objects.get(email=email)

            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)

            reset_link = (
                f"http://127.0.0.1:8000/reset-password/"
                f"?uid={uid}&token={token}"
            )

            send_mail(
                subject="HELPNET Password Reset",
                message=(
                    "You requested a password reset for your HELPNET account.\n\n"
                    f"Reset your password using this link:\n{reset_link}\n\n"
                    "If you did not request this, you can ignore this email."
                ),
                from_email=None,
                recipient_list=[user.email],
                fail_silently=False,
            )

        except User.DoesNotExist:
            pass

        return Response(
            {
                "success": True,
                "data": None,
                "message": (
                    "If an account exists with this email, "
                    "a password reset link has been sent."
                )
            },
            status=status.HTTP_200_OK
        )

class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                {
                    "success": False,
                    "data": None,
                    "message": serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        uid = serializer.validated_data["uid"]
        token = serializer.validated_data["token"]
        new_password = serializer.validated_data["new_password"]

        try:
            user_id = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk=user_id)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response(
                {
                    "success": False,
                    "data": None,
                    "message": "Invalid password reset link."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        if not default_token_generator.check_token(user, token):
            return Response(
                {
                    "success": False,
                    "data": None,
                    "message": "Invalid or expired password reset link."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        user.set_password(new_password)
        user.save()

        return Response(
            {
                "success": True,
                "data": None,
                "message": "Password reset successful."
            },
            status=status.HTTP_200_OK
        )


# remove the duplicate "from .serializers import RegisterSerializer"


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Return the currently logged-in user's profile."""
        serializer = UserProfileSerializer(request.user)
        return Response(
            {
                "success": True,
                "data": serializer.data,
                "message": "Profile loaded.",
            },
            status=status.HTTP_200_OK,
        )

    def patch(self, request):
        """Update editable fields of the profile."""
        serializer = UserProfileSerializer(
            request.user, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(
                {
                    "success": True,
                    "data": serializer.data,
                    "message": "Profile updated.",
                },
                status=status.HTTP_200_OK,
            )
        return Response(
            {"success": False, "data": None, "message": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )


class PublicUserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id):
        user = get_object_or_404(User, user_id=user_id)
        serializer = PublicUserProfileSerializer(user)
        return Response(
            {
                "success": True,
                "data": serializer.data,
                "message": "User profile loaded.",
            },
            status=status.HTTP_200_OK,
        )