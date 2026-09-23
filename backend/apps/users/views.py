from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .permissions import IsAdminRole
from .serializers import RegisterSerializer


User = get_user_model()


class RegisterView(APIView):

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


# ==========================================
# S2-T06 SECURITY TEST
# ==========================================

# TEST 1: NO TOKEN
class ProtectedView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(
            {
                "success": True,
                "message": "Access granted.",
                "user": request.user.email,
            }
        )


# TEST 2: WRONG ROLE
class AdminOnlyView(APIView):

    permission_classes = [IsAdminRole]

    def get(self, request):
        return Response(
            {
                "success": True,
                "message": "Admin access granted.",
            }
        )