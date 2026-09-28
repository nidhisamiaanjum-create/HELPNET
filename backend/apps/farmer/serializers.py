from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import ProduceListing

User = get_user_model()


class FarmerContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "user_id",
            "full_name",
            "phone_number",
            "email",
            "location",
            "role",
            "is_verified",
        ]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Farmer's allowed contact info:
        # In marketplace, phone is primary contact channel. If is_phone_visible is False, show phone for produce listing contact unless private.
        # However ST 44 specifies: "Show farmer's allowed contact information".
        # We respect user privacy flags while making sure full_name & phone are properly provided.
        if not getattr(instance, "is_email_visible", False):
            data["email"] = None
        return data


class ProduceListingSerializer(serializers.ModelSerializer):
    farmer_name = serializers.CharField(source="farmer.full_name", read_only=True)
    farmer_phone = serializers.CharField(source="farmer.phone_number", read_only=True)
    farmer_location = serializers.CharField(source="farmer.location", read_only=True)
    farmer_verified = serializers.BooleanField(source="farmer.is_verified", read_only=True)
    farmer_details = FarmerContactSerializer(source="farmer", read_only=True)
    is_owner = serializers.SerializerMethodField()

    class Meta:
        model = ProduceListing
        fields = [
            "id",
            "farmer",
            "farmer_name",
            "farmer_phone",
            "farmer_location",
            "farmer_verified",
            "farmer_details",
            "produce_name",
            "category",
            "price",
            "unit",
            "quantity",
            "availability",
            "location",
            "description",
            "is_owner",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "farmer", "created_at", "updated_at"]

    def get_is_owner(self, obj):
        request = self.context.get("request")
        if request and request.user and request.user.is_authenticated:
            return obj.farmer_id == request.user.user_id
        return False

    def create(self, validated_data):
        validated_data["farmer"] = self.context["request"].user
        return super().create(validated_data)
