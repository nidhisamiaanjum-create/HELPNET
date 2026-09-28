import uuid
from django.conf import settings
from django.db import models


class WastePickupRequest(models.Model):
    class WasteType(models.TextChoices):
        ORGANIC = "Organic", "Organic / Kitchen Waste"
        RECYCLABLE = "Recyclable", "Recyclable / Plastic & Paper"
        ELECTRONIC = "Electronic", "Electronic / E-Waste"
        HAZARDOUS = "Hazardous", "Hazardous / Medical Waste"
        BULK = "Bulk", "Bulk / Construction Waste"
        GENERAL = "General", "General / Other Waste"

    class Status(models.TextChoices):
        REQUESTED = "Requested", "Requested"
        CONTACTED = "Contacted", "Contacted"
        COMPLETED = "Completed", "Completed"
        CANCELLED = "Cancelled", "Cancelled"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    requester = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="waste_requests",
    )
    waste_type = models.CharField(
        max_length=50,
        choices=WasteType.choices,
        default=WasteType.GENERAL,
    )
    area = models.CharField(max_length=100)
    location = models.CharField(max_length=255)
    preferred_pickup_date = models.DateField(null=True, blank=True)
    preferred_pickup_time = models.CharField(max_length=50, blank=True)
    preferred_datetime = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.REQUESTED,
    )
    notes = models.TextField(blank=True)
    collector = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="collected_waste_requests",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.waste_type} pickup at {self.area} ({self.status})"
