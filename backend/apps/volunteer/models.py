from django.conf import settings
from django.db import models


class VolunteerProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="volunteer_profile")
    skills = models.TextField(blank=True, help_text="Comma-separated skills")
    availability = models.CharField(max_length=255, blank=True)
    location = models.CharField(max_length=255, blank=True)
    blood_group = models.CharField(max_length=3, blank=True)
    supporting_certificates = models.TextField(blank=True, help_text="Certificate names or links")
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Volunteer profile: {self.user.full_name}"


class VolunteerOpportunity(models.Model):
    class Status(models.TextChoices):
        OPEN = "Open", "Open"
        CLOSED = "Closed", "Closed"

    title = models.CharField(max_length=200)
    description = models.TextField()
    date = models.DateField()
    location = models.CharField(max_length=255)
    required_volunteers = models.PositiveIntegerField()
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.OPEN)
    coordinator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="volunteer_opportunities")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["date", "title"]

    def __str__(self):
        return self.title


class VolunteerSignup(models.Model):
    volunteer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="volunteer_signups")
    event = models.ForeignKey(VolunteerOpportunity, on_delete=models.CASCADE, related_name="signups")
    signed_up_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["volunteer", "event"], name="unique_volunteer_event_signup")]
        ordering = ["signed_up_at"]


class VolunteerAttendance(models.Model):
    volunteer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="volunteer_attendance")
    event = models.ForeignKey(VolunteerOpportunity, on_delete=models.CASCADE, related_name="attendance")
    check_in_time = models.DateTimeField(null=True, blank=True)
    check_out_time = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["volunteer", "event"], name="unique_volunteer_event_attendance")]


class VolunteerMessage(models.Model):
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="volunteer_messages")
    event = models.ForeignKey(VolunteerOpportunity, on_delete=models.CASCADE, related_name="messages")
    message = models.TextField(max_length=2000)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["timestamp"]


class VolunteerCertificate(models.Model):
    volunteer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="volunteer_certificates")
    event = models.ForeignKey(VolunteerOpportunity, on_delete=models.CASCADE, related_name="certificates")
    coordinator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="issued_volunteer_certificates")
    completion_date = models.DateField()
    issued_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["volunteer", "event"], name="unique_volunteer_event_certificate")]
