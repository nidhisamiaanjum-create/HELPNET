from rest_framework import serializers
from .models import User
from .models import UserProfile
from apps.ratings.models import Rating


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        min_length=8
    )

    class Meta:
        model = User
        fields = [
            "full_name",
            "email",
            "phone_number",
            "password",
            "location",
        ]

    def to_internal_value(self, data):
        forbidden = {"role", "is_staff", "is_superuser", "is_admin"}.intersection(data)
        if forbidden:
            raise serializers.ValidationError({key: "This field cannot be set during registration." for key in sorted(forbidden)})
        return super().to_internal_value(data)

    def validate_phone_number(self, value):
        if User.objects.filter(phone_number=value).exists():
            raise serializers.ValidationError(
                "This phone number is already registered."
            )
        return value

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                "This email is already registered."
            )
        return value

    def create(self, validated_data):
        password = validated_data.pop("password")

        user = User.objects.create_user(
            password=password,
            **validated_data
        )

        return user


class RoleProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ("id", "profile_type", "display_name", "status", "created_at", "updated_at")
        read_only_fields = ("id", "status", "created_at", "updated_at")

    def validate_profile_type(self, value):
        if value not in UserProfile.Type.values:
            raise serializers.ValidationError("Choose a supported profile type.")
        return value

class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(
        write_only=True,
        min_length=8
    )

class UserProfileSerializer(serializers.ModelSerializer):
    average_rating = serializers.SerializerMethodField()
    rating_count = serializers.SerializerMethodField()

    def get_average_rating(self, user):
        return Rating.average_for_user(user)

    def get_rating_count(self, user):
        return user.ratings_received.count()

    class Meta:
        model = User
        fields = [
            "user_id",
            "full_name",
            "email",
            "phone_number",
            "role",
            "location",
            "bio",
            "profile_picture",
            "is_verified",
            "date_of_birth",
            "gender",
            "is_phone_visible",
            "is_email_visible",
            "is_location_visible",
            "is_date_of_birth_visible",
            "average_rating",
            "rating_count",
        ]
        read_only_fields = ["user_id", "email", "phone_number", "role"]


class PublicUserProfileSerializer(serializers.ModelSerializer):
    average_rating = serializers.SerializerMethodField()
    rating_count = serializers.SerializerMethodField()

    def get_average_rating(self, user):
        return Rating.average_for_user(user)

    def get_rating_count(self, user):
        return user.ratings_received.count()

    class Meta:
        model = User
        fields = [
            "user_id",
            "full_name",
            "role",
            "location",
            "bio",
            "profile_picture",
            "is_verified",
            "average_rating",
            "rating_count",
        ]
        read_only_fields = fields
