from django.shortcuts import render
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from django.utils import timezone
from django.shortcuts import get_object_or_404

from apps.users.permissions import IsAdminUserRole
from .services import create_admin_action_log
from .models import VerificationRequest, AdminActionLog

def nid_verification_page(request):
    return render(request, "apps.verification/nid-verification.html")


class VerificationSubmitView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        document_type = request.data.get("document_type")
        document = request.FILES.get("document")

        allowed_types = {
            VerificationRequest.DocumentType.NID,
            VerificationRequest.DocumentType.PASSPORT,
            VerificationRequest.DocumentType.BIRTH_CERTIFICATE,
        }

        if document_type not in allowed_types:
            return Response(
                {
                    "success": False,
                    "message": "Invalid document type."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not document:
            return Response(
                {
                    "success": False,
                    "message": "Document file is required."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if document.size > 5 * 1024 * 1024:
            return Response(
                {
                    "success": False,
                    "message": "File size must not exceed 5 MB."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        allowed_mime_types = {
            "image/jpeg",
            "image/png",
            "application/pdf",
        }

        if document.content_type not in allowed_mime_types:
            return Response(
                {
                    "success": False,
                    "message": "Only JPG, PNG or PDF files are allowed."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        existing_request = (
            VerificationRequest.objects
            .filter(
                user=request.user,
                status=VerificationRequest.Status.PENDING,
            )
            .first()
        )

        if existing_request:
            return Response(
                {
                    "success": False,
                    "message": "You already have a pending verification request."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        verification_request = VerificationRequest.objects.create(
            user=request.user,
            document_type=document_type,
            document=document,
            status=VerificationRequest.Status.PENDING,
        )

        return Response(
            {
                "success": True,
                "data": {
                    "id": str(verification_request.id),
                    "document_type": verification_request.document_type,
                    "status": verification_request.status,
                    "submitted_at": verification_request.submitted_at,
                },
                "message": "Verification request submitted successfully.",
            },
            status=status.HTTP_201_CREATED,
        )

class VerificationStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        verification_request = (
            VerificationRequest.objects
            .filter(user=request.user)
            .first()
        )

        if not verification_request:
            return Response(
                {
                    "success": True,
                    "data": {
                        "status": "unverified",
                        "document_type": None,
                        "rejection_reason": "",
                        "submitted_at": None,
                    },
                    "message": "No verification request found.",
                },
                status=status.HTTP_200_OK,
            )

        return Response(
            {
                "success": True,
                "data": {
                    "status": verification_request.status,
                    "document_type": verification_request.document_type,
                    "rejection_reason": verification_request.rejection_reason,
                    "submitted_at": verification_request.submitted_at,
                },
                "message": "Verification status retrieved successfully.",
            },
            status=status.HTTP_200_OK,
        )

class AdminVerificationListView(APIView):
    permission_classes = [IsAdminUserRole]

    def get(self, request):
        requests = (
            VerificationRequest.objects
            .select_related("user")
            .filter(status=VerificationRequest.Status.PENDING)
        )

        data = []

        for verification_request in requests:
            data.append(
                {
                    "id": str(verification_request.id),
                    "user_id": str(verification_request.user.user_id),
                    "full_name": verification_request.user.full_name,
                    "email": verification_request.user.email,
                    "phone_number": verification_request.user.phone_number,
                    "document_type": verification_request.document_type,
                    "document_url": (
                        request.build_absolute_uri(
                            verification_request.document.url
                        )
                        if verification_request.document
                        else None
                    ),
                    "submitted_at": verification_request.submitted_at,
                    "status": verification_request.status,
                }
            )

        return Response(
            {
                "success": True,
                "data": data,
                "message": "Pending verification requests retrieved successfully.",
            },
            status=status.HTTP_200_OK,
        )

class AdminVerificationActionView(APIView):
    permission_classes = [IsAdminUserRole]

    def post(self, request, verification_id):
        verification_request = get_object_or_404(
            VerificationRequest.objects.select_related("user"),
            id=verification_id,
        )

        if verification_request.status != VerificationRequest.Status.PENDING:
            return Response(
                {
                    "success": False,
                    "message": "This verification request has already been reviewed.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        action = request.data.get("action")
        reason = request.data.get("reason", "").strip()

        if action not in {"approve", "reject"}:
            return Response(
                {
                    "success": False,
                    "message": "Action must be approve or reject.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if action == "reject" and not reason:
            return Response(
                {
                    "success": False,
                    "message": "Rejection reason is required.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if action == "approve":
            verification_request.status = VerificationRequest.Status.APPROVED
            verification_request.rejection_reason = ""
            verification_request.user.is_verified = True
            verification_request.user.save(update_fields=["is_verified"])

            log_action = AdminActionLog.Action.APPROVE
            message = "Verification request approved successfully."

        else:
            verification_request.status = VerificationRequest.Status.REJECTED
            verification_request.rejection_reason = reason

            log_action = AdminActionLog.Action.REJECT
            message = "Verification request rejected."

        verification_request.reviewed_at = timezone.now()
        verification_request.reviewed_by = request.user
        verification_request.save(
            update_fields=[
                "status",
                "rejection_reason",
                "reviewed_at",
                "reviewed_by",
            ]
        )

        create_admin_action_log(
            admin=request.user,
            action=log_action,
            target_user=verification_request.user,
            target_reference=str(verification_request.id),
            reason=reason,
        )

        return Response(
            {
                "success": True,
                "data": {
                    "id": str(verification_request.id),
                    "status": verification_request.status,
                    "rejection_reason": verification_request.rejection_reason,
                    "reviewed_at": verification_request.reviewed_at,
                },
                "message": message,
            },
            status=status.HTTP_200_OK,
        )
class AdminActionLogListView(APIView):
    permission_classes = [IsAdminUserRole]

    def get(self, request):
        logs = (
            AdminActionLog.objects
            .select_related("admin", "target_user")
            .all()
        )

        data = []

        for log in logs:
            data.append(
                {
                    "id": str(log.id),
                    "admin_name": log.admin.full_name,
                    "admin_email": log.admin.email,
                    "action": log.action,
                    "action_label": log.get_action_display(),
                    "target_user": (
                        log.target_user.full_name
                        if log.target_user
                        else None
                    ),
                    "target_reference": log.target_reference,
                    "reason": log.reason,
                    "timestamp": log.timestamp,
                }
            )

        return Response(
            {
                "success": True,
                "data": data,
                "message": "Admin action logs retrieved successfully.",
            },
            status=status.HTTP_200_OK,
        )
