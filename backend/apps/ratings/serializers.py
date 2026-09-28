from rest_framework import serializers
from .models import Rating


class RatingSerializer(serializers.ModelSerializer):
    rater_name = serializers.CharField(source="rater.full_name", read_only=True)
    rated_user_name = serializers.CharField(source="rated_user.full_name", read_only=True)

    class Meta:
        model = Rating
        fields = [
            "id",
            "rater",
            "rater_name",
            "rated_user",
            "rated_user_name",
            "score",
            "comment",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "rater", "created_at", "updated_at"]

    def create(self, validated_data):
        rater = self.context["request"].user
        rated_user = validated_data["rated_user"]

        if rater == rated_user:
            raise serializers.ValidationError({"detail": "You cannot rate yourself."})

        # Update existing rating or create new
        rating, created = Rating.objects.update_or_create(
            rater=rater,
            rated_user=rated_user,
            defaults={
                "score": validated_data["score"],
                "comment": validated_data.get("comment", ""),
            }
        )
        return rating
