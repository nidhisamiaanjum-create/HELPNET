import uuid

from django.conf import settings
from django.db import models


class VerificationRequest(models.Model):
    class DocumentType(models.TextChoices):
        NID = "nid", "National ID"
        PASSPORT = "passport", "Passport"
        BIRTH_CERTIFICATE = "birth_certificate", "Birth certificate"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="verification_requests",
    )
    document_type = models.CharField(max_length=30, choices=DocumentType.choices)
    document = models.FileField(upload_to="verification_documents/")
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    rejection_reason = models.TextField(blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(blank=True, null=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="verification_requests_reviewed",
    )

    class Meta:
        ordering = ["-submitted_at"]

    def __str__(self):
        return f"{self.user} — {self.get_document_type_display()} ({self.status})"


class AdminActionLog(models.Model):
    class Action(models.TextChoices):
        APPROVE = "approve", "Approve"
        REJECT = "reject", "Reject"
        MODERATION = "moderation", "Moderation"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    admin = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="admin_action_logs",
    )
    action = models.CharField(max_length=20, choices=Action.choices)
    target_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="actions_received",
    )
    target_reference = models.CharField(max_length=255, blank=True)
    reason = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.admin} {self.action} at {self.timestamp:%Y-%m-%d %H:%M}"
