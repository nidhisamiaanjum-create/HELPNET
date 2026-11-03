from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.conf import settings
from django.core.mail import send_mail
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import EmailValidator
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.encoding import force_bytes, force_str
from django.utils import timezone
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from pathlib import Path
from django.db import DatabaseError
from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.db.models import Q
# at the top, with other imports:
from .serializers import (
    RegisterSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
    UserProfileSerializer,
    PublicUserProfileSerializer,
    RoleProfileSerializer,
)
from .models import NGOVerificationDocument, UserProfile
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.exceptions import ValidationError
from django.db import IntegrityError, transaction
from .permissions import IsAdminUserRole

User = get_user_model()


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.save()
            profile = user.active_profile

            return Response(
                {
                "success": True,
                "data": {
                    "user_id": str(user.user_id),
                    "full_name": user.full_name,
                    "email": user.email,
                    "phone_number": user.phone_number,
                    "role": user.role,
                    "active_profile": {
                        "id": profile.id,
                        "profile_type": profile.profile_type,
                        "status": profile.status,
                        "ngo_approval_status": profile.ngo_approval_status,
                    },
                    "profiles": [
                        {
                            "id": item.id,
                            "profile_type": item.profile_type,
                            "status": item.status,
                            "ngo_approval_status": item.ngo_approval_status,
                        }
                        for item in user.profiles.all()
                    ],
                },
                "message": (
                    "Registration successful. Submit NGO information and documents to request verification."
                    if profile.profile_type == UserProfile.Type.NGO
                    else "Registration successful."
                ),
            },
            status=status.HTTP_201_CREATED,
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

        import time

        total_start = time.perf_counter()

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

        # 1. Database lookup
        start = time.perf_counter()

        try:
            if "@" in identifier:
                user = User.objects.get(email=identifier)
            else:
                user = User.objects.get(phone_number=identifier)
        except User.DoesNotExist:
            user = None

        print(
            "LOGIN - USER LOOKUP:",
            round((time.perf_counter() - start) * 1000, 2),
            "ms"
        )

        # 2. Password check
        user_exists = user is not None

        print(
            "LOGIN - USER EXISTS:",
            user_exists
        )

        # 2. Password check
        print("LOGIN - PASSWORD START")

        start = time.perf_counter()

        password_valid = user.check_password(password) if user else False

        end = time.perf_counter()

        print(
               "LOGIN - PASSWORD END"
                )

        print(
               "LOGIN - PASSWORD ONLY:",
               round((end - start) * 1000, 2),
               "ms"
                )

        if not password_valid:
            return Response(
                {
                    "success": False,
                    "data": None,
                    "message": "Invalid email/phone number or password."
                },
                status=status.HTTP_401_UNAUTHORIZED
            )

        # 3. JWT generation
        start = time.perf_counter()

        refresh = RefreshToken.for_user(user)

        print(
            "LOGIN - JWT GENERATION:",
            round((time.perf_counter() - start) * 1000, 2),
            "ms"
        )

        # 4. Total
        print(
            "LOGIN - TOTAL:",
            round((time.perf_counter() - total_start) * 1000, 2),
            "ms"
        )

        return Response(
            {
                "success": True,
                "data": {
                    "user_id": str(user.user_id),
                    "full_name": user.full_name,
                    "email": user.email,
                    "phone_number": user.phone_number,
                    "role": user.role,
                    "is_staff": user.is_staff,
                    "is_superuser": user.is_superuser,
                    "access": str(refresh.access_token),
                    "refresh": str(refresh),
                },
                "message": "Login successful."
            },
            status=status.HTTP_200_OK
        )


class LogoutView(APIView):
    def post(self, request):
        import time

        total_start = time.perf_counter()

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
            start = time.perf_counter()

            token = RefreshToken(refresh_token)

            print(
                "LOGOUT - TOKEN PARSE:",
                round((time.perf_counter() - start) * 1000, 2),
                "ms"
            )

            start = time.perf_counter()

            token.blacklist()

            print(
                "LOGOUT - BLACKLIST:",
                round((time.perf_counter() - start) * 1000, 2),
                "ms"
            )

            print(
                "LOGOUT - TOTAL:",
                round((time.perf_counter() - total_start) * 1000, 2),
                "ms"
            )

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
                f"{settings.FRONTEND_BASE_URL}/reset-password/"
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

    def get_user_data(self, user):
        data = dict(UserProfileSerializer(user).data)
        data["is_staff"] = user.is_staff
        data["is_superuser"] = user.is_superuser
        data["role"] = user.role or ""
        return data

    def get(self, request):
        return Response({
            "success": True,
            "data": self.get_user_data(request.user),
            "message": "Profile loaded.",
        }, status=status.HTTP_200_OK)

    def patch(self, request):
        serializer = UserProfileSerializer(
            request.user,
            data=request.data,
            partial=True,
        )

        if serializer.is_valid():
            serializer.save()

            return Response({
                "success": True,
                "data": self.get_user_data(request.user),
                "message": "Profile updated.",
            }, status=status.HTTP_200_OK)

        return Response({
            "success": False,
            "data": None,
            "message": serializer.errors,
        }, status=status.HTTP_400_BAD_REQUEST)


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

class UserSearchView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        query = request.query_params.get("q", "").strip()

        if not query:
            return Response(
                {
                    "success": True,
                    "data": [],
                    "message": "Enter a name, role, or area to search.",
                },
                status=status.HTTP_200_OK,
            )

        users = (
            User.objects
            .filter(
                Q(full_name__icontains=query)
                | Q(role__icontains=query)
                | Q(location__icontains=query)
            )
            .exclude(user_id=request.user.user_id)
            .filter(is_active=True)
            .order_by("full_name")[:20]
        )

        results = []

        for user in users:
            results.append({
                "user_id": str(user.user_id),
                "full_name": user.full_name,
                "role": user.role,
                "location": user.location or "",
            })

        return Response(
            {
                "success": True,
                "data": results,
                "message": f"{len(results)} user(s) found.",
            },
            status=status.HTTP_200_OK,
        )


class UserProfilesView(ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = RoleProfileSerializer

    def get_queryset(self):
        return UserProfile.objects.filter(user=self.request.user).order_by("created_at")

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        data = self.get_serializer(queryset, many=True).data
        return Response({
            "success": True,
            "data": data,
            "message": "Profiles loaded.",
        })

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        profile_type = serializer.validated_data["profile_type"]
        extra = request.data.get("details") or {}
        if not isinstance(extra, dict):
            raise ValidationError({"details": "Expected an object."})
        if profile_type == UserProfile.Type.NGO:
            if extra:
                raise ValidationError({
                    "details": "NGO applications currently use the profile display name and account details."
                })
            display_name = str(
                request.data.get("display_name", "")
            ).strip()
            if not display_name:
                raise ValidationError({
                    "display_name": "Organization/profile name is required."
                })
            profile = serializer.save(
                user=request.user,
                display_name=display_name,
                ngo_approval_status=UserProfile.NGOApprovalStatus.PENDING,
            )
            data = self.get_serializer(profile).data
            return Response(
                {
                    "success": True,
                    "data": data,
                    "message": (
                        "NGO profile created. Submit organization information "
                        "and registration documents to request verification."
                    ),
                },
                status=status.HTTP_201_CREATED,
            )
        try:
            with transaction.atomic():
                profile = serializer.save(user=request.user)
                if profile_type == UserProfile.Type.VOLUNTEER:
                    from apps.volunteer.models import VolunteerProfile
                    VolunteerProfile.objects.create(user=request.user, **{
                        key: extra[key] for key in ("skills", "availability", "location", "blood_group", "supporting_certificates") if key in extra
                    })
                elif profile_type == UserProfile.Type.BLOOD_DONOR:
                    from apps.blood.models import DonorProfile
                    if not extra.get("blood_group") or not extra.get("area"):
                        raise ValidationError({"details": "blood_group and area are required for a Blood Donor profile."})
                    valid_groups = [choice[0] for choice in DonorProfile._meta.get_field("blood_group").choices]
                    if extra["blood_group"] not in valid_groups:
                        raise ValidationError({"details": {"blood_group": "Choose a valid blood group."}})
                    DonorProfile.objects.create(user=request.user, blood_group=extra["blood_group"], area=extra["area"])
                elif profile_type == UserProfile.Type.FARMER and extra:
                    raise ValidationError({"details": "Farmer profile details are managed through the farmer marketplace."})
        except IntegrityError:
            raise ValidationError({"profile_type": "You already have this profile type."})
        data = self.get_serializer(profile).data
        return Response({"success": True, "data": data, "message": "Profile created."}, status=status.HTTP_201_CREATED)

class PendingNGOApprovalListView(APIView):
    permission_classes = [IsAdminUserRole]

    def get(self, request):
        profiles = (
            UserProfile.objects
            .filter(
                profile_type=UserProfile.Type.NGO,
                ngo_verification_status__in=[
                    UserProfile.NGOVerificationStatus.PENDING,
                    UserProfile.NGOVerificationStatus.UNDER_REVIEW,
                    UserProfile.NGOVerificationStatus.ADDITIONAL_DOCUMENTS_REQUIRED,
                ],
            )
            .select_related("user")
            .prefetch_related("ngo_verification_documents")
            .order_by("created_at")
        )

        data = []
        for profile in profiles:
            data.append({
                "profile_id": profile.id,
                "user_id": str(profile.user_id),
                "display_name": profile.display_name,
                "full_name": profile.user.full_name,
                "email": profile.user.email,
                "phone_number": profile.user.phone_number,
                "location": profile.user.location or "",
                "created_at": profile.created_at.isoformat(),
                "ngo_approval_status": profile.ngo_approval_status,
                "ngo_registration_number": profile.ngo_registration_number,
                "ngo_address": profile.ngo_address,
                "ngo_contact_email": profile.ngo_contact_email,
                "ngo_contact_phone": profile.ngo_contact_phone,
                "ngo_representative_name": profile.ngo_representative_name,
                "ngo_verification_status": profile.ngo_verification_status,
                "ngo_verification_reason": profile.ngo_verification_reason,
                "ngo_submitted_at": (
                    profile.ngo_submitted_at.isoformat()
                    if profile.ngo_submitted_at
                    else None
                ),
                "ngo_reviewed_at": (
                    profile.ngo_reviewed_at.isoformat()
                    if profile.ngo_reviewed_at
                    else None
                ),
                "documents": [
                    ngo_document_data(document)
                    for document in profile.ngo_verification_documents.all()
                ],
            })

        return Response({
            "success": True,
            "data": data,
            "count": len(data),
        }, status=status.HTTP_200_OK)


class NGOApprovalView(APIView):
    permission_classes = [IsAdminUserRole]

    def patch(self, request, profile_id):
        profile = get_object_or_404(
            UserProfile,
            id=profile_id,
            profile_type=UserProfile.Type.NGO,
        )

        verification_status = request.data.get(
            "verification_status",
            request.data.get("approval_status"),
        )
        legacy_status_map = {
            UserProfile.NGOApprovalStatus.APPROVED:
                UserProfile.NGOVerificationStatus.APPROVED,
            UserProfile.NGOApprovalStatus.REJECTED:
                UserProfile.NGOVerificationStatus.REJECTED,
        }
        verification_status = legacy_status_map.get(
            verification_status,
            verification_status,
        )
        allowed_statuses = {
            UserProfile.NGOVerificationStatus.UNDER_REVIEW,
            UserProfile.NGOVerificationStatus.APPROVED,
            UserProfile.NGOVerificationStatus.REJECTED,
            UserProfile.NGOVerificationStatus.ADDITIONAL_DOCUMENTS_REQUIRED,
        }

        if verification_status not in allowed_statuses:
            return Response(
                {
                    "success": False,
                    "message": (
                        "Choose under_review, approved, rejected, or "
                        "additional_documents_required."
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        reason = str(request.data.get("review_reason", "")).strip()
        if verification_status in {
            UserProfile.NGOVerificationStatus.REJECTED,
            UserProfile.NGOVerificationStatus.ADDITIONAL_DOCUMENTS_REQUIRED,
        } and not reason:
            return Response(
                {
                    "success": False,
                    "message": "A review reason is required for this decision.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        if verification_status == UserProfile.NGOVerificationStatus.APPROVED:
            required_fields = (
                "display_name",
                "ngo_registration_number",
                "ngo_address",
                "ngo_contact_email",
                "ngo_contact_phone",
                "ngo_representative_name",
            )
            has_required_information = all(
                getattr(profile, field).strip()
                for field in required_fields
            )
            has_registration_certificate = profile.ngo_verification_documents.filter(
                document_type=(
                    NGOVerificationDocument.DocumentType
                    .REGISTRATION_CERTIFICATE
                )
            ).exists()
            if not has_required_information or not has_registration_certificate:
                return Response(
                    {
                        "success": False,
                        "message": (
                            "Complete all required NGO information and submit "
                            "a registration certificate before approval."
                        ),
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        profile.ngo_verification_status = verification_status
        profile.ngo_approval_status = (
            UserProfile.NGOApprovalStatus.APPROVED
            if verification_status == UserProfile.NGOVerificationStatus.APPROVED
            else UserProfile.NGOApprovalStatus.REJECTED
            if verification_status == UserProfile.NGOVerificationStatus.REJECTED
            else UserProfile.NGOApprovalStatus.PENDING
        )
        profile.ngo_verification_reason = reason
        profile.ngo_reviewed_at = timezone.now()
        profile.save(
            update_fields=[
                "ngo_verification_status",
                "ngo_approval_status",
                "ngo_verification_reason",
                "ngo_reviewed_at",
                "updated_at",
            ]
        )

        return Response(
            {
                "success": True,
                "message": f"NGO verification {verification_status}.",
                "data": {
                    "profile_id": profile.id,
                    "user_id": str(profile.user_id),
                    "profile_type": profile.profile_type,
                    "status": profile.status,
                    "ngo_approval_status": profile.ngo_approval_status,
                    "ngo_verification_status": (
                        profile.ngo_verification_status
                    ),
                    "ngo_verification_reason": (
                        profile.ngo_verification_reason
                    ),
                    "ngo_reviewed_at": (
                        profile.ngo_reviewed_at.isoformat()
                        if profile.ngo_reviewed_at
                        else None
                    ),
                },
            },
            status=status.HTTP_200_OK,
        )


def ngo_document_data(document):
    return {
        "id": str(document.id),
        "document_type": document.document_type,
        "name": document.original_name,
        "uploaded_at": document.uploaded_at.isoformat(),
        "download_url": reverse(
            "ngo-verification-document",
            kwargs={"document_id": document.id},
        ),
    }


def validate_ngo_document(uploaded):
    if uploaded.size > 10 * 1024 * 1024:
        raise ValidationError(
            {"documents": f"{uploaded.name} must be 10 MB or smaller."}
        )

    extension = Path(uploaded.name).suffix.lower()
    signatures = {
        ".pdf": ("application/pdf", lambda data: data.startswith(b"%PDF-")),
        ".jpg": ("image/jpeg", lambda data: data.startswith(b"\xff\xd8\xff")),
        ".jpeg": ("image/jpeg", lambda data: data.startswith(b"\xff\xd8\xff")),
        ".png": (
            "image/png",
            lambda data: data.startswith(b"\x89PNG\r\n\x1a\n"),
        ),
    }
    expected = signatures.get(extension)
    if not expected:
        raise ValidationError(
            {"documents": f"{uploaded.name} must be a PDF, JPG, or PNG."}
        )

    uploaded.seek(0)
    signature = uploaded.read(8)
    uploaded.seek(0)
    if uploaded.content_type != expected[0] or not expected[1](signature):
        raise ValidationError(
            {"documents": f"{uploaded.name} is not a valid {extension[1:].upper()} file."}
        )


class NGOVerificationSubmissionView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get_profile(self, request, profile_id):
        profile = get_object_or_404(
            UserProfile,
            id=profile_id,
            user=request.user,
            profile_type=UserProfile.Type.NGO,
            status=UserProfile.Status.ACTIVE,
        )
        if request.user.active_profile_id != profile.id:
            raise ValidationError(
                {"profile": "Select this active NGO profile before verification."}
            )
        return profile

    def get(self, request, profile_id):
        profile = self.get_profile(request, profile_id)
        data = RoleProfileSerializer(profile).data
        data["documents"] = [
            ngo_document_data(document)
            for document in profile.ngo_verification_documents.all()
        ]
        return Response({"success": True, "data": data})

    def post(self, request, profile_id):
        profile = self.get_profile(request, profile_id)
        resubmittable_statuses = {
            UserProfile.NGOVerificationStatus.NOT_SUBMITTED,
            UserProfile.NGOVerificationStatus.REJECTED,
            UserProfile.NGOVerificationStatus.ADDITIONAL_DOCUMENTS_REQUIRED,
        }
        if profile.ngo_verification_status not in resubmittable_statuses:
            raise ValidationError(
                {"status": "This application cannot be changed while it is under review or approved."}
            )

        fields = {
            "display_name": str(
                request.data.get("organization_name", "")
            ).strip(),
            "ngo_registration_number": str(
                request.data.get("registration_number", "")
            ).strip(),
            "ngo_address": str(request.data.get("organization_address", "")).strip(),
            "ngo_contact_email": str(
                request.data.get("official_contact_email", "")
            ).strip(),
            "ngo_contact_phone": str(
                request.data.get("contact_phone", "")
            ).strip(),
            "ngo_representative_name": str(
                request.data.get("representative_name", "")
            ).strip(),
        }
        errors = {
            key: "This field is required."
            for key, value in fields.items()
            if not value
        }
        try:
            EmailValidator()(fields["ngo_contact_email"])
        except DjangoValidationError:
            errors["official_contact_email"] = "Enter a valid email address."
        if len(fields["ngo_registration_number"]) > 100:
            errors["registration_number"] = "Ensure this value is at most 100 characters."
        if len(fields["ngo_contact_phone"]) > 30:
            errors["contact_phone"] = "Ensure this value is at most 30 characters."
        if len(fields["ngo_representative_name"]) > 150:
            errors["representative_name"] = "Ensure this value is at most 150 characters."
        if errors:
            raise ValidationError(errors)

        files_by_type = {
            NGOVerificationDocument.DocumentType.REGISTRATION_CERTIFICATE:
                request.FILES.getlist("registration_certificate"),
            NGOVerificationDocument.DocumentType.OFFICIAL_DOCUMENT:
                request.FILES.getlist("official_documents"),
            NGOVerificationDocument.DocumentType.AUTHORIZATION_LETTER:
                request.FILES.getlist("authorization_letters"),
            NGOVerificationDocument.DocumentType.SUPPORTING_DOCUMENT:
                request.FILES.getlist("supporting_documents"),
        }
        for uploaded_files in files_by_type.values():
            for uploaded in uploaded_files:
                validate_ngo_document(uploaded)

        if (
            profile.ngo_verification_status
            == UserProfile.NGOVerificationStatus.ADDITIONAL_DOCUMENTS_REQUIRED
            and not any(files_by_type.values())
        ):
            raise ValidationError({
                "documents": (
                    "Upload at least one additional or replacement document."
                )
            })

        existing_certificate = profile.ngo_verification_documents.filter(
            document_type=(
                NGOVerificationDocument.DocumentType.REGISTRATION_CERTIFICATE
            )
        ).exists()
        if not files_by_type[
            NGOVerificationDocument.DocumentType.REGISTRATION_CERTIFICATE
        ] and not existing_certificate:
            raise ValidationError({
                "registration_certificate": (
                    "Upload the NGO registration certificate."
                )
            })

        stored_files = []
        try:
            with transaction.atomic():
                for field, value in fields.items():
                    setattr(profile, field, value)
                profile.ngo_verification_status = (
                    UserProfile.NGOVerificationStatus.PENDING
                )
                profile.ngo_approval_status = (
                    UserProfile.NGOApprovalStatus.PENDING
                )
                profile.ngo_verification_reason = ""
                profile.ngo_submitted_at = timezone.now()
                profile.ngo_reviewed_at = None
                profile.save()

                for document_type, uploaded_files in files_by_type.items():
                    if not uploaded_files:
                        continue
                    old_documents = list(
                        profile.ngo_verification_documents.filter(
                            document_type=document_type
                        )
                    )
                    for old_document in old_documents:
                        old_name = old_document.file.name
                        transaction.on_commit(
                            lambda storage=old_document.file.storage, name=old_name:
                                storage.delete(name)
                        )
                        old_document.delete()

                    for uploaded in uploaded_files:
                        document = NGOVerificationDocument(
                            profile=profile,
                            document_type=document_type,
                            original_name=Path(uploaded.name).name[:255],
                        )
                        document.file.save(
                            uploaded.name,
                            uploaded,
                            save=False,
                        )
                        stored_files.append(
                            (document.file.storage, document.file.name)
                        )
                        document.save()
        except (DatabaseError, OSError, ValueError):
            for storage, name in stored_files:
                storage.delete(name)
            raise

        data = RoleProfileSerializer(profile).data
        data["documents"] = [
            ngo_document_data(document)
            for document in profile.ngo_verification_documents.all()
        ]
        return Response(
            {
                "success": True,
                "data": data,
                "message": "NGO verification application submitted.",
            },
            status=status.HTTP_200_OK,
        )


class NGOVerificationDocumentDownloadView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, document_id):
        document = get_object_or_404(
            NGOVerificationDocument.objects.select_related("profile"),
            id=document_id,
        )
        if (
            not request.user.is_superuser
            and document.profile.user_id != request.user.user_id
        ):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied(
                "Only the NGO owner and authorized administrators may access this document."
            )

        try:
            file_handle = document.file.open("rb")
        except FileNotFoundError as error:
            raise Http404("The verification document is no longer available.") from error

        response = FileResponse(
            file_handle,
            as_attachment=True,
            filename=document.original_name,
        )
        response["X-Content-Type-Options"] = "nosniff"
        response["Cache-Control"] = "private, no-store"
        return response


class UserProfileDetailView(RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = RoleProfileSerializer
    lookup_field = "id"

    def get_queryset(self):
        return UserProfile.objects.filter(user=self.request.user)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        # Profiles are permanent once created: type cannot be exchanged.
        if "profile_type" in request.data:
            raise ValidationError({
                "profile_type": (
                    "Profile type cannot be changed after creation."
                )
            })
        if "user" in request.data or "user_id" in request.data:
            raise ValidationError({
                "user": "Profiles cannot be moved to another account."
            })
        details = request.data.get("details")
        if "details" in request.data and not isinstance(details, dict):
            raise ValidationError({"details": "Expected an object."})
        instance = self.get_object()
        serializer = self.get_serializer(
            instance,
            data=request.data,
            partial=partial,
        )
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            self.perform_update(serializer)
            if "details" in request.data:
                self._update_profile_details(
                    serializer.instance,
                    details,
                )
            return Response(
                self.get_serializer(serializer.instance).data,
                status=status.HTTP_200_OK,
            )

    def _update_profile_details(self, profile, details):
        if not details:
            return
        if profile.profile_type == UserProfile.Type.VOLUNTEER:
            from apps.volunteer.models import VolunteerProfile
            from apps.volunteer.serializers import VolunteerProfileSerializer

            allowed_fields = {
                "skills",
                "availability",
                "location",
                "blood_group",
                "supporting_certificates",
            }
            unknown_fields = set(details) - allowed_fields
            if unknown_fields:
                raise ValidationError({
                    "details": {
                        field: "This field cannot be changed for a volunteer profile."
                        for field in sorted(unknown_fields)
                    }
                })
            volunteer_profile = get_object_or_404(
                VolunteerProfile,
                user=profile.user,
            )
            serializer = VolunteerProfileSerializer(
                volunteer_profile,
                data=details,
                partial=True,
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return

        if profile.profile_type == UserProfile.Type.BLOOD_DONOR:
            from apps.blood.models import BloodGroup, DonorProfile

            donor_profile = get_object_or_404(
                DonorProfile,
                user=profile.user,
            )
            allowed_fields = {"blood_group", "area", "availability"}
            unknown_fields = set(details) - allowed_fields
            if unknown_fields:
                raise ValidationError({
                    "details": {
                        field: "This field cannot be changed for a donor profile."
                        for field in sorted(unknown_fields)
                    }
                })

            blood_group = details.get(
                "blood_group",
                donor_profile.blood_group,
            )
            area = str(details.get("area", donor_profile.area)).strip()
            availability = details.get(
                "availability",
                donor_profile.availability,
            )
            errors = {}
            if blood_group not in BloodGroup.values:
                errors["blood_group"] = "Select a valid blood group."
            if not area:
                errors["area"] = "Area is required."
            if availability not in DonorProfile.Availability.values:
                errors["availability"] = "Select a valid donor availability."
            if errors:
                raise ValidationError({"details": errors})

            donor_profile.blood_group = blood_group
            donor_profile.area = area
            donor_profile.availability = availability
            donor_profile.save(
                update_fields=[
                    "blood_group",
                    "area",
                    "availability",
                    "updated_at",
                ]
            )
            return

        raise ValidationError({
            "details": "This profile type has no separate editable details."
        })

    def perform_update(self, serializer):
        serializer.save(user=self.request.user)

    def perform_destroy(self, instance):
        # Deactivate to preserve role-specific records and activity history.
        if self.request.user.active_profile_id == instance.id:
            self.request.user.active_profile = None
            self.request.user.role = ""
            self.request.user.save(update_fields=["active_profile", "role"])
        instance.status = UserProfile.Status.INACTIVE
        instance.save(update_fields=["status", "updated_at"])


class ReactivateUserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, profile_id):
        profile = get_object_or_404(
            UserProfile,
            id=profile_id,
            user=request.user,
            status=UserProfile.Status.INACTIVE,
        )
        profile.status = UserProfile.Status.ACTIVE
        profile.save(update_fields=["status", "updated_at"])
        return Response(
            {
                "success": True,
                "data": RoleProfileSerializer(profile).data,
                "message": "Profile reactivated. Select it to use this profile.",
            },
            status=status.HTTP_200_OK,
        )


class ActiveProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile = request.user.active_profile
        if profile and profile.user_id == request.user.user_id and profile.status == UserProfile.Status.ACTIVE:
            data = RoleProfileSerializer(profile).data
        else:
            data = None
        return Response({"success": True, "data": data, "message": "Active profile loaded."})

    def put(self, request):
        profile = get_object_or_404(UserProfile, id=request.data.get("profile_id"), user=request.user, status=UserProfile.Status.ACTIVE)
        request.user.active_profile = profile
        role_map = {"citizen": "Citizen", "volunteer": "Volunteer", "farmer": "Farmer", "ngo": "NGO", "blood_donor": "Blood Donor"}
        # Keep legacy modules working by reflecting the server-selected profile.
        # Staff/superuser authority remains independent of this business role.
        request.user.role = role_map[profile.profile_type]
        request.user.save(update_fields=["active_profile", "role"])
        return Response({"success": True, "data": RoleProfileSerializer(profile).data, "message": "Active profile updated."})
