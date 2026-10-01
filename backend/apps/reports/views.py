from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from apps.verification.models import AdminActionLog
from apps.verification.services import create_admin_action_log
from .models import Report
from .serializers import ReportSerializer


class ReportListCreateView(generics.ListCreateAPIView):
    serializer_class = ReportSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.role == "Admin":
            return Report.objects.select_related("reporter", "reported_user", "content_type").all()
        return Report.objects.filter(reporter=user)

    def perform_create(self, serializer):
        serializer.save(reporter=self.request.user)


class ReportModerationView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    TARGET_MODELS = {
        "blood.bloodrequest": ("requester",),
        "goods.goodslisting": ("seller",),
        "farmer.producelisting": ("farmer",),
        "volunteer.volunteeropportunity": ("coordinator",),
    }

    def is_admin(self, user):
        return user.role == "Admin" or user.is_staff or user.is_superuser

    def get(self, request):
        if not self.is_admin(request.user):
            return Response({"success": False, "message": "Administrator access required."}, status=status.HTTP_403_FORBIDDEN)
        model_key = str(request.query_params.get("content_type", "")).lower()
        if model_key not in self.TARGET_MODELS:
            return Response({"success": False, "message": "Select a supported content type."}, status=status.HTTP_400_BAD_REQUEST)
        content_type = ContentType.objects.get_by_natural_key(*model_key.split(".", 1))
        model = content_type.model_class()
        items = []
        excluded = {"farmer", "seller", "requester", "coordinator", "created_at", "updated_at"}
        for item in model.objects.all():
            editable = {
                field.name: getattr(item, field.name)
                for field in model._meta.concrete_fields
                if field.editable and not field.primary_key and field.name not in excluded
                and field.get_internal_type() not in {"FileField", "ImageField"}
            }
            editable = {
                field.name: field.value_to_string(item)
                for field in model._meta.concrete_fields
                if field.name in editable
            }
            items.append({"id": str(item.pk), "summary": str(item), "editable": editable})
        return Response({"success": True, "data": items})

    def post(self, request):
        if not self.is_admin(request.user):
            return Response({"success": False, "message": "Administrator access required."}, status=status.HTTP_403_FORBIDDEN)

        report_id = request.data.get("report_id")
        action = request.data.get("action")
        report = None
        if report_id:
            report = Report.objects.select_related("content_type", "reported_user").filter(pk=report_id).first()
            if report is None or report.content_type_id is None or report.object_id is None:
                return Response({"success": False, "message": "Report or reported content was not found."}, status=status.HTTP_404_NOT_FOUND)
            model_key = f"{report.content_type.app_label}.{report.content_type.model}"
            object_id = report.object_id
        else:
            model_key = str(request.data.get("content_type", "")).lower()
            object_id = str(request.data.get("object_id", ""))

        if action == "review" and report is not None:
            with transaction.atomic():
                report.status = Report.Status.REVIEWED
                report.save(update_fields=["status", "updated_at"])
                create_admin_action_log(
                    admin=request.user,
                    action=AdminActionLog.Action.MODERATION,
                    target_user=report.reported_user,
                    target_reference=f"review:report:{report.pk}",
                    reason=str(request.data.get("reason", "")).strip(),
                )
            return Response({"success": True, "message": "Report reviewed."})

        if action not in {"edit", "remove"} or model_key not in self.TARGET_MODELS or not object_id:
            return Response({"success": False, "message": "Select a supported content item and moderation action."}, status=status.HTTP_400_BAD_REQUEST)

        content_type = ContentType.objects.get_by_natural_key(*model_key.split(".", 1))
        model = content_type.model_class()
        item = model.objects.filter(pk=object_id).first() if model else None
        if item is None:
            return Response({"success": False, "message": "Reported content was not found."}, status=status.HTTP_404_NOT_FOUND)
        owner = next((getattr(item, field, None) for field in self.TARGET_MODELS[model_key] if getattr(item, field, None)), None)
        reason = str(request.data.get("reason", "")).strip()
        target_reference = f"{model_key}:{object_id}"

        try:
            with transaction.atomic():
                if action == "edit":
                    changes = request.data.get("changes")
                    if not isinstance(changes, dict) or not changes:
                        return Response({"success": False, "message": "Provide the content changes to save."}, status=status.HTTP_400_BAD_REQUEST)
                    editable = {field.name: field for field in model._meta.concrete_fields if field.editable and not field.primary_key}
                    if any(key not in editable or key in {"farmer", "seller", "requester", "coordinator", "created_at", "updated_at"} for key in changes):
                        return Response({"success": False, "message": "One or more fields cannot be edited."}, status=status.HTTP_400_BAD_REQUEST)
                    for key, value in changes.items():
                        setattr(item, key, value)
                    item.full_clean()
                    item.save(update_fields=list(changes.keys()))
                else:
                    item.delete()
                create_admin_action_log(
                    admin=request.user,
                    action=AdminActionLog.Action.MODERATION,
                    target_user=owner,
                    target_reference=f"{action}:{target_reference}",
                    reason=reason,
                )
        except Exception as exc:
            return Response({"success": False, "message": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"success": True, "message": "Content updated." if action == "edit" else "Content removed."})
