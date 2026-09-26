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
