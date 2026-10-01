from rest_framework import serializers
from .models import Report


class ReportSerializer(serializers.ModelSerializer):
    reporter_name = serializers.CharField(source="reporter.full_name", read_only=True)
    reported_user_name = serializers.CharField(source="reported_user.full_name", read_only=True)
    content_type = serializers.SerializerMethodField()
    content_summary = serializers.SerializerMethodField()

    def get_content_type(self, obj):
        if obj.content_type_id is None:
            return ""
        return f"{obj.content_type.app_label}.{obj.content_type.model}"

    def get_content_summary(self, obj):
        target = obj.content_object
        if target is None:
            return ""
        return str(target)

    class Meta:
        model = Report
        fields = [
            "id",
            "reporter",
            "reporter_name",
            "reported_user",
            "reported_user_name",
            "content_type",
            "object_id",
            "content_summary",
            "category",
            "description",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "reporter", "status", "created_at", "updated_at", "content_type", "object_id", "content_summary"]

    def create(self, validated_data):
        reporter = self.context["request"].user
        validated_data["reporter"] = reporter
        return super().create(validated_data)
