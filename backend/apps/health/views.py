import mimetypes

from django.db import transaction
from django.db.models import Count, IntegerField, OuterRef, Subquery, Value
from django.db.models.functions import Coalesce
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import parsers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.permissions import IsAdminUserRole
from apps.users.permissions import IsCitizenUser
from apps.verification.models import AdminActionLog
from apps.verification.services import create_admin_action_log
from .models import HealthProfessional, HealthQuestion, HealthReply
from .serializers import (
    HealthProfessionalApplicationSerializer,
    HealthProfessionalSerializer,
    HealthQuestionSerializer,
    HealthReplySerializer,
)


class HealthQuestionListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    @staticmethod
    def question_queryset():
        reply_counts = (
            HealthReply.objects.filter(question_id=OuterRef("pk"))
            .order_by()
            .values("question_id")
            .annotate(total=Count("pk"))
            .values("total")[:1]
        )
        return (
            HealthQuestion.objects.select_related("author")
            .annotate(
                reply_count=Coalesce(Subquery(reply_counts), Value(0), output_field=IntegerField()),
            )
        )

    def get(self, request):
        questions = []
        seen_questions = set()
        for question in self.question_queryset():
            signature = (question.author_id, question.title, question.description, question.category)
            if signature not in seen_questions:
                seen_questions.add(signature)
                questions.append(question)
        return Response({"success": True, "data": HealthQuestionSerializer(questions, many=True).data, "message": "Health questions loaded."})

    def post(self, request):
        serializer = HealthQuestionSerializer(data=request.data)
        if serializer.is_valid():
            duplicate = HealthQuestion.objects.filter(
                author=request.user,
                title=serializer.validated_data["title"],
                description=serializer.validated_data["description"],
                category=serializer.validated_data["category"],
            ).first()
            if duplicate:
                duplicate.reply_count = duplicate.replies.count()
                return Response({"success": True, "data": HealthQuestionSerializer(duplicate).data, "message": "This question has already been submitted."})
            question = serializer.save(author=request.user)
            question.reply_count = 0
            return Response({"success": True, "data": HealthQuestionSerializer(question).data, "message": "Question created."}, status=status.HTTP_201_CREATED)
        return Response({"success": False, "data": None, "message": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class HealthQuestionDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, question_id):
        question = get_object_or_404(HealthQuestionListCreateView.question_queryset(), pk=question_id)
        return Response({"success": True, "data": HealthQuestionSerializer(question).data, "message": "Question loaded."})


class HealthReplyListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, question_id):
        get_object_or_404(HealthQuestion, pk=question_id)
        replies = HealthReply.objects.filter(question_id=question_id).select_related("author")
        return Response({"success": True, "data": HealthReplySerializer(replies, many=True).data, "message": "Replies loaded."})

    def post(self, request, question_id):
        question = get_object_or_404(HealthQuestion, pk=question_id)
        serializer = HealthReplySerializer(data=request.data)
        if serializer.is_valid():
            reply = serializer.save(author=request.user, question=question)
            return Response({"success": True, "data": HealthReplySerializer(reply).data, "message": "Reply added."}, status=status.HTTP_201_CREATED)
        return Response({"success": False, "data": None, "message": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class HealthProfessionalListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        professionals = HealthProfessional.objects.select_related("user").filter(
            verification_status=HealthProfessional.VerificationStatus.VERIFIED
        )
        return Response({"success": True, "data": HealthProfessionalSerializer(professionals, many=True).data, "message": "Health professionals loaded."})


class HealthProfessionalApplicationView(APIView):
    permission_classes = [IsCitizenUser]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]

    @staticmethod
    def serialize_application(application):
        if not application:
            return {
                "status": "not_submitted",
                "rejection_reason": "",
                "submitted": False,
            }
        return {
            "id": application.pk,
            "name": application.name,
            "profession": application.profession,
            "specialization": application.specialization,
            "location": application.location,
            "contact": application.contact,
            "credential_type": application.credential_type,
            "credential_number": application.credential_number,
            "status": application.verification_status,
            "rejection_reason": application.rejection_reason,
            "submitted": True,
        }

    def get(self, request):
        application = HealthProfessional.objects.filter(user=request.user).order_by("-pk").first()
        return Response({"success": True, "data": self.serialize_application(application)})

    @transaction.atomic
    def post(self, request):
        serializer = HealthProfessionalApplicationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"success": False, "message": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        request.user.__class__.objects.select_for_update().get(pk=request.user.pk)
        application = HealthProfessional.objects.filter(user=request.user).order_by("-pk").first()
        if application and (
            application.verification_status == HealthProfessional.VerificationStatus.VERIFIED
            or (
                application.verification_status == HealthProfessional.VerificationStatus.PENDING
                and bool(application.credential_document)
            )
        ):
            return Response(
                {"success": False, "message": "An application is already pending or approved."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        values = serializer.validated_data.copy()
        document = values.pop("credential_document")
        if application:
            previous_document = application.credential_document
            for field, value in values.items():
                setattr(application, field, value)
            application.user = request.user
            application.verification_status = HealthProfessional.VerificationStatus.PENDING
            application.rejection_reason = ""
            application.reviewed_at = None
            application.reviewed_by = None
            application.credential_document = document
            application.save()
            if previous_document:
                previous_document.delete(save=False)
        else:
            application = HealthProfessional.objects.create(
                user=request.user,
                **values,
                credential_document=document,
                verification_status=HealthProfessional.VerificationStatus.PENDING,
            )
        return Response(
            {
                "success": True,
                "data": self.serialize_application(application),
                "message": "Health professional application submitted for admin review.",
            },
            status=status.HTTP_201_CREATED,
        )


class AdminHealthProfessionalApplicationsView(APIView):
    permission_classes = [IsAdminUserRole]

    def get(self, request):
        applications = HealthProfessional.objects.filter(
            verification_status=HealthProfessional.VerificationStatus.PENDING,
        ).exclude(credential_document="").select_related("user").order_by("id")
        return Response({
            "success": True,
            "data": [{
                "id": item.pk,
                "user_id": str(item.user_id) if item.user_id else None,
                "name": item.name,
                "profession": item.profession,
                "specialization": item.specialization,
                "location": item.location,
                "contact": item.contact,
                "credential_type": item.credential_type,
                "credential_number": item.credential_number,
                "document_name": item.credential_document.name.rsplit("/", 1)[-1],
                "applicant_phone": item.user.phone_number if item.user_id else "",
                "document_url": f"/api/health/professionals/admin/{item.pk}/document/",
            } for item in applications],
        })


class AdminHealthProfessionalDocumentView(APIView):
    permission_classes = [IsAdminUserRole]

    def get(self, request, professional_id):
        application = get_object_or_404(
            HealthProfessional,
            pk=professional_id,
        )
        if not application.credential_document:
            return Response({"success": False, "message": "Credential document is not available."}, status=status.HTTP_404_NOT_FOUND)
        content_type = mimetypes.guess_type(application.credential_document.name)[0] or "application/octet-stream"
        return FileResponse(
            application.credential_document.open("rb"),
            as_attachment=True,
            filename=application.credential_document.name.rsplit("/", 1)[-1],
            content_type=content_type,
        )


class HealthProfessionalVerificationView(APIView):
    permission_classes = [IsAdminUserRole]

    def patch(self, request, professional_id):
        professional = get_object_or_404(HealthProfessional, pk=professional_id)
        action = request.data.get("action")
        new_status = request.data.get("verification_status")
        if action in {"approve", "reject"}:
            new_status = (
                HealthProfessional.VerificationStatus.VERIFIED
                if action == "approve"
                else HealthProfessional.VerificationStatus.REJECTED
            )
        if new_status not in {
            HealthProfessional.VerificationStatus.VERIFIED,
            HealthProfessional.VerificationStatus.REJECTED,
        }:
            return Response({"success": False, "message": "Choose approve or reject."}, status=status.HTTP_400_BAD_REQUEST)
        if professional.verification_status != HealthProfessional.VerificationStatus.PENDING:
            return Response({"success": False, "message": "This application has already been reviewed."}, status=status.HTTP_400_BAD_REQUEST)
        if new_status == HealthProfessional.VerificationStatus.VERIFIED and not professional.credential_document:
            return Response({"success": False, "message": "A submitted credential document is required for approval."}, status=status.HTTP_400_BAD_REQUEST)
        reason = str(request.data.get("reason", "")).strip()
        if new_status == HealthProfessional.VerificationStatus.REJECTED and not reason:
            return Response({"success": False, "message": "A rejection reason is required."}, status=status.HTTP_400_BAD_REQUEST)
        with transaction.atomic():
            professional.verification_status = new_status
            professional.rejection_reason = reason if new_status == HealthProfessional.VerificationStatus.REJECTED else ""
            professional.reviewed_at = timezone.now()
            professional.reviewed_by = request.user
            professional.save(update_fields=["verification_status", "rejection_reason", "reviewed_at", "reviewed_by"])
            create_admin_action_log(
                admin=request.user,
                action=AdminActionLog.Action.APPROVE if new_status == HealthProfessional.VerificationStatus.VERIFIED else AdminActionLog.Action.REJECT,
                target_user=professional.user,
                target_reference=f"health-professional:{professional.pk}",
                reason=professional.rejection_reason,
            )
        return Response({"success": True, "data": HealthProfessionalSerializer(professional).data, "message": "Professional application reviewed."})
