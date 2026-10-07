import uuid

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Avg


class Rating(models.Model):
    """A single user's rating of another user.

    TODO: When an interaction model exists, scope the unique constraint to it.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    rater = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="ratings_given",
    )
    rated_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="ratings_received",
    )
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["rater", "rated_user"],
                name="unique_rating_per_rater_and_user",
            )
        ]
        ordering = ["-created_at"]

    @classmethod
    def average_for_user(cls, user):
        return cls.objects.filter(rated_user=user).aggregate(average=Avg("rating"))["average"]

    def __str__(self):
        return f"{self.rater} rated {self.rated_user}: {self.rating}/5"
