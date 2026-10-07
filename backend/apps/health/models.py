from django.conf import settings
from django.db import models


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
    verification_status = models.CharField(max_length=12, choices=VerificationStatus.choices, default=VerificationStatus.PENDING)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name
