from rest_framework import serializers

from .models import (
    WasteCollector,
    WasteCollectorRating,
    WastePickupRequest,
)


class WasteCollectorRatingSerializer(
    serializers.ModelSerializer
):
    user_name = serializers.CharField(
        source="user.full_name",
        read_only=True,
    )

    class Meta:
        model = WasteCollectorRating

        fields = [
            "id",
            "collector",
            "user",
            "user_name",
            "rating",
            "review",
            "created_at",
        ]

        read_only_fields = [
            "id",
            "collector",
            "user",
            "user_name",
            "created_at",
        ]

    def validate_rating(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError(
                "Rating must be between 1 and 5."
            )

        return value


class WasteCollectorSerializer(
    serializers.ModelSerializer
):
    shared_by_name = serializers.CharField(
        source="shared_by.full_name",
        read_only=True,
    )

    average_rating = serializers.FloatField(
        read_only=True,
    )

    rating_count = serializers.IntegerField(
        read_only=True,
    )

    user_rating = serializers.SerializerMethodField()

    class Meta:
        model = WasteCollector

        fields = [
            "id",
            "name",
            "phone",
            "area",
            "waste_types",
            "notes",
            "shared_by_name",
            "created_at",
            "average_rating",
            "rating_count",
            "user_rating",
        ]

        read_only_fields = [
            "id",
            "shared_by_name",
            "created_at",
            "average_rating",
            "rating_count",
            "user_rating",
        ]

    def get_user_rating(self, obj):
        request = self.context.get("request")

        if not request or not request.user.is_authenticated:
            return None

        rating = obj.ratings.filter(
            user=request.user
        ).first()

        if not rating:
            return None

        return {
            "rating": rating.rating,
            "review": rating.review,
        }


class WastePickupRequestSerializer(
    serializers.ModelSerializer
):
    requester_name = serializers.CharField(
        source="requester.full_name",
        read_only=True,
    )

    requester_phone = serializers.CharField(
        source="requester.phone_number",
        read_only=True,
    )

    collector_details = WasteCollectorSerializer(
        source="collector",
        read_only=True,
    )

    class Meta:
        model = WastePickupRequest

        fields = [
            "id",
            "requester",
            "requester_name",
            "requester_phone",
            "waste_type",
            "area",
            "location",
            "preferred_pickup_date",
            "preferred_pickup_time",
            "preferred_datetime",
            "status",
            "notes",
            "collector",
            "collector_details",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "requester",
            "created_at",
            "updated_at",
        ]

    def create(self, validated_data):
        validated_data["requester"] = (
            self.context["request"].user
        )

        return super().create(validated_data)