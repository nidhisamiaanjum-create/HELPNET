
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

        if not getattr(instance, "is_phone_visible", False):
            data["phone_number"] = None
        if not getattr(instance, "is_location_visible", False):
            data["location"] = None

        # Hide email if the farmer has not enabled email visibility.
        if not getattr(instance, "is_email_visible", False):
            data["email"] = None

        return data


class ProduceListingSerializer(serializers.ModelSerializer):
    # Farmer information
    farmer_name = serializers.CharField(
        source="farmer.full_name",
        read_only=True
    )
    farmer_phone = serializers.SerializerMethodField()
    farmer_location = serializers.SerializerMethodField()
    farmer_verified = serializers.BooleanField(
        source="farmer.is_verified",
        read_only=True
    )
    farmer_details = FarmerContactSerializer(
        source="farmer",
        read_only=True
    )
    is_owner = serializers.SerializerMethodField()

    # Reject negative prices
    price = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=0
    )

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
        read_only_fields = [
            "id",
            "farmer",
            "created_at",
            "updated_at",
        ]

    def get_is_owner(self, obj):
        request = self.context.get("request")

        if request and request.user and request.user.is_authenticated:
            return obj.farmer_id == request.user.user_id

        return False

    def get_farmer_phone(self, obj):
        return obj.farmer.phone_number if obj.farmer.is_phone_visible else None

    def get_farmer_location(self, obj):
        return obj.farmer.location if obj.farmer.is_location_visible else None

    def create(self, validated_data):
        # Assign the listing to the authenticated farmer.
        validated_data["farmer"] = self.context["request"].user

        return super().create(validated_data)
