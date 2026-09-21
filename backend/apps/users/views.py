from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

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
        email = request.data.get("email")
        password = request.data.get("password")

        # Check required fields
        if not email or not password:
            return Response(
                {
                    "success": False,
                    "data": None,
                    "message": "Email and password are required."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # Find user using email
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            user = None

        # Check password
        if user is None or not user.check_password(password):
            return Response(
                {
                    "success": False,
                    "data": None,
                    "message": "Invalid email or password."
                },
                status=status.HTTP_401_UNAUTHORIZED
            )

        # Create JWT tokens
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