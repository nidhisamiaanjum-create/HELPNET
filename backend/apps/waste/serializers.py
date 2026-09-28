from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import WastePickupRequest

User = get_user_model()


class CollectorUserSerializer(serializers.ModelSerializer):
    average_rating = serializers.SerializerMethodField()
    rating_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "user_id",
            "full_name",
            "phone_number",
            "email",
            "role",
            "location",
            "average_rating",
            "rating_count",
        ]

    def get_average_rating(self, obj):
        # Using Rating model if exists
        try:
            from apps.ratings.models import Rating
            avg = Rating.average_for_user(obj)
            return round(avg, 1) if avg is not None else 5.0
        except Exception:
            return 5.0

    def get_rating_count(self, obj):
        try:
            from apps.ratings.models import Rating
            return Rating.objects.filter(rated_user=obj).count()
        except Exception:
            return 0


class WastePickupRequestSerializer(serializers.ModelSerializer):
    requester_name = serializers.CharField(source="requester.full_name", read_only=True)
    requester_phone = serializers.CharField(source="requester.phone_number", read_only=True)
    collector_details = CollectorUserSerializer(source="collector", read_only=True)

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
        read_only_fields = ["id", "requester", "created_at", "updated_at"]

    def create(self, validated_data):
        validated_data["requester"] = self.context["request"].user
        return super().create(validated_data)
