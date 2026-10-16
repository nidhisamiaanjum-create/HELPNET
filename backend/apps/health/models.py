from django.conf import settings
from django.db import models

from .storage import HealthCredentialStorage


class HealthQuestion(models.Model):
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="health_questions")
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=80)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class HealthReply(models.Model):
    question = models.ForeignKey(HealthQuestion, on_delete=models.CASCADE, related_name="replies")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="health_replies")
    reply = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"Reply by {self.author} on {self.question}"


class HealthProfessional(models.Model):
    class VerificationStatus(models.TextChoices):
        PENDING = "pending", "Pending"
        VERIFIED = "verified", "Verified"
        REJECTED = "rejected", "Rejected"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="health_professional_profiles")
    name = models.CharField(max_length=150)
    profession = models.CharField(max_length=100)
    specialization = models.CharField(max_length=150, blank=True)
    location = models.CharField(max_length=255, blank=True)
    contact = models.CharField(max_length=255, blank=True)
    credential_type = models.CharField(max_length=100, blank=True)
    credential_number = models.CharField(max_length=100, blank=True)
    credential_document = models.FileField(
        storage=HealthCredentialStorage(),
        upload_to="health_credentials/%Y/%m/",
        blank=True,
        null=True,
    )
    rejection_reason = models.TextField(blank=True)
    reviewed_at = models.DateTimeField(blank=True, null=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="health_professional_reviews",
    )
    verification_status = models.CharField(max_length=12, choices=VerificationStatus.choices, default=VerificationStatus.PENDING)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name
