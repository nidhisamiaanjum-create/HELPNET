from rest_framework import serializers
from .models import Report


class ReportSerializer(serializers.ModelSerializer):
    reporter_name = serializers.CharField(source="reporter.full_name", read_only=True)
    reported_user_name = serializers.CharField(source="reported_user.full_name", read_only=True)

    class Meta:
        model = Report
        fields = [
            "id",
            "reporter",
            "reporter_name",
            "reported_user",
            "reported_user_name",
            "category",
            "description",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "reporter", "status", "created_at", "updated_at"]

    def create(self, validated_data):
        reporter = self.context["request"].user
        validated_data["reporter"] = reporter
        return super().create(validated_data)
