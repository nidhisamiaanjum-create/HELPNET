import uuid
from django.conf import settings
from django.db import models


class ProduceListing(models.Model):
    class Availability(models.TextChoices):
        AVAILABLE = "Available", "Available"
        UNAVAILABLE = "Unavailable", "Unavailable"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    farmer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="produce_listings",
    )
    produce_name = models.CharField(max_length=150)
    category = models.CharField(max_length=50, blank=True, default="Vegetables")
    price = models.DecimalField(max_digits=10, decimal_places=2)
    unit = models.CharField(max_length=30, default="kg")
    quantity = models.CharField(max_length=100)
    availability = models.CharField(
        max_length=20,
        choices=Availability.choices,
        default=Availability.AVAILABLE,
    )
    location = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.produce_name} by {self.farmer} - {self.price}/{self.unit} ({self.availability})"
