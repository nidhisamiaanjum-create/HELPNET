from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import F, Q


class GoodsListing(models.Model):
    class Condition(models.TextChoices):
        NEW = "New", "New"
        LIKE_NEW = "Like new", "Like new"
        GOOD = "Good", "Good"
        FAIR = "Fair", "Fair"
        FOR_PARTS = "For parts", "For parts"

    class Status(models.TextChoices):
        AVAILABLE = "Available", "Available"
        RESERVED = "Reserved", "Reserved"
        EXCHANGED = "Exchanged", "Exchanged"
        REMOVED = "Removed", "Removed"

    seller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="goods_listings")
    title = models.CharField(max_length=200)
    description = models.TextField()
    condition = models.CharField(max_length=20, choices=Condition.choices)
    asking_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    location = models.CharField(max_length=255)
    image = models.ImageField(upload_to="goods_images/", blank=True, null=True)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.AVAILABLE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class GoodsInterest(models.Model):
    listing = models.ForeignKey(GoodsListing, on_delete=models.CASCADE, related_name="interests")
    interested_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="goods_interests")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["listing", "interested_user"], name="unique_goods_interest_per_user_listing")]
        ordering = ["-created_at"]


class GoodsConversation(models.Model):
    listing = models.ForeignKey(GoodsListing, on_delete=models.CASCADE, related_name="conversations")
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="goods_conversations_as_owner")
    interested_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="goods_conversations_as_interested")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["listing", "owner", "interested_user"], name="unique_goods_conversation_pair"),
            models.CheckConstraint(condition=~Q(owner=F("interested_user")), name="goods_conversation_distinct_participants"),
        ]
        ordering = ["-updated_at"]


class GoodsMessage(models.Model):
    conversation = models.ForeignKey(GoodsConversation, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="goods_messages")
    message = models.CharField(max_length=2000)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at", "pk"]


class GoodsReport(models.Model):
    class Status(models.TextChoices):
        OPEN = "Open", "Open"
        REVIEWED = "Reviewed", "Reviewed"
        RESOLVED = "Resolved", "Resolved"

    listing = models.ForeignKey(GoodsListing, on_delete=models.CASCADE, related_name="reports")
    reporter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="goods_reports")
    reason = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.OPEN)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
