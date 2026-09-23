from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated

from .serializers import RegisterSerializer
from .permissions import IsAdminRole


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

        # Temporary debugging
        print("LOGIN DEBUG")
        print("Identifier:", identifier)
        print("User found:", user is not None)

        if user is not None:
            print("User email:", user.email)
            print("User phone:", user.phone_number)
            print("Password valid:", user.check_password(password))

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



class AdminOnlyView(APIView):

    permission_classes = [IsAdminRole]

    def get(self, request):

        return Response(
            {
                "success": True,
                "message": "Admin access granted.",
            }
        )