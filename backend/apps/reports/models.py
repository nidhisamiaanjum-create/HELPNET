import uuid
from django.conf import settings
from django.db import models


class Report(models.Model):
    class Category(models.TextChoices):
        NO_SHOW = "no_show", "No show / Did not arrive"
        UNPROFESSIONAL = "unprofessional", "Unprofessional behavior"
        OVERCHARGING = "overcharging", "Overcharging / Payment dispute"
        HARASSMENT = "harassment", "Inappropriate behavior / Harassment"
        FRAUD = "fraud", "Fraud / False information"
        OTHER = "other", "Other"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        REVIEWED = "reviewed", "Reviewed"
        RESOLVED = "resolved", "Resolved"
        DISMISSED = "dismissed", "Dismissed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reports_submitted",
    )
    reported_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reports_received",
    )
    category = models.CharField(
        max_length=50,
        choices=Category.choices,
        default=Category.OTHER,
    )
    description = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Report by {self.reporter} against {self.reported_user} ({self.category})"
