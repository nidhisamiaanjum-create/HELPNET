import re

from django.db.models import Avg
from rest_framework import serializers

from .models import HealthProfessional, HealthQuestion, HealthReply


class HealthQuestionSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source="author.full_name", read_only=True)
    author_is_verified = serializers.BooleanField(source="author.is_verified", read_only=True)
    reply_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = HealthQuestion
        fields = ["id", "author", "author_name", "author_is_verified", "title", "description", "category", "created_at", "reply_count"]
        read_only_fields = ["id", "author", "author_name", "author_is_verified", "created_at", "reply_count"]


class HealthReplySerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source="author.full_name", read_only=True)
    author_is_verified = serializers.BooleanField(source="author.is_verified", read_only=True)
    author_average_rating = serializers.SerializerMethodField()
    author_rating_count = serializers.SerializerMethodField()

    class Meta:
        model = HealthReply
        fields = ["id", "question", "author", "author_name", "author_is_verified", "author_average_rating", "author_rating_count", "reply", "created_at"]
        read_only_fields = ["id", "question", "author", "author_name", "author_is_verified", "author_average_rating", "author_rating_count", "created_at"]

    def get_author_average_rating(self, obj):
        from apps.ratings.models import Rating
        return Rating.objects.filter(rated_user=obj.author).aggregate(value=Avg("rating"))["value"]

    def get_author_rating_count(self, obj):
        from apps.ratings.models import Rating
        return Rating.objects.filter(rated_user=obj.author).count()


class HealthProfessionalSerializer(serializers.ModelSerializer):
    is_verified = serializers.SerializerMethodField()
    user_is_verified = serializers.BooleanField(source="user.is_verified", read_only=True, allow_null=True)
    average_rating = serializers.SerializerMethodField()
    rating_count = serializers.SerializerMethodField()

    class Meta:
        model = HealthProfessional
        fields = ["id", "user", "user_is_verified", "name", "profession", "specialization", "location", "contact", "verification_status", "is_verified", "average_rating", "rating_count"]
        read_only_fields = fields

    def get_is_verified(self, obj):
        return obj.verification_status == HealthProfessional.VerificationStatus.VERIFIED

    def get_average_rating(self, obj):
        if not obj.user_id:
            return None
        from apps.ratings.models import Rating
        return Rating.objects.filter(rated_user_id=obj.user_id).aggregate(value=Avg("rating"))["value"]

    def get_rating_count(self, obj):
        if not obj.user_id:
            return 0
        from apps.ratings.models import Rating
        return Rating.objects.filter(rated_user_id=obj.user_id).count()


class HealthProfessionalApplicationSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=150)
    profession = serializers.CharField(max_length=100)
    specialization = serializers.CharField(max_length=150, required=False, allow_blank=True)
    location = serializers.CharField(max_length=255, required=False, allow_blank=True)
    contact = serializers.CharField(max_length=255)
    credential_type = serializers.CharField(max_length=100)
    credential_number = serializers.CharField(max_length=100)
    credential_document = serializers.FileField(allow_empty_file=False)

    def validate_contact(self, value):
        value = value.strip()
        is_email = re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", value)
        digits = re.sub(r"\D", "", value)
        is_phone = bool(re.fullmatch(r"[+()\d.\s-]+", value) and 7 <= len(digits) <= 15)
        if not is_email and not is_phone:
            raise serializers.ValidationError("Enter a valid phone number or email address for direct contact.")
        return value

    def validate_credential_document(self, document):
        if document.size > 5 * 1024 * 1024:
            raise serializers.ValidationError("Credential documents must be 5 MB or smaller.")

        prefix = document.read(8)
        document.seek(0)
        valid = (
            (document.content_type == "application/pdf" and prefix.startswith(b"%PDF-"))
            or (document.content_type == "image/jpeg" and prefix.startswith(b"\xff\xd8\xff"))
            or (document.content_type == "image/png" and prefix.startswith(b"\x89PNG\r\n\x1a\n"))
        )
        if not valid:
            raise serializers.ValidationError("Upload a valid PDF, JPG, or PNG credential document.")
        return document
