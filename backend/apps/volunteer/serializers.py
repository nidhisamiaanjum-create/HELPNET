from rest_framework import serializers
from .models import VolunteerOpportunity, VolunteerProfile, VolunteerSignup, VolunteerAttendance, VolunteerMessage, VolunteerCertificate


class VolunteerOpportunitySerializer(serializers.ModelSerializer):
    coordinator_name = serializers.CharField(source="coordinator.full_name", read_only=True)
    signup_count = serializers.SerializerMethodField()

    def get_signup_count(self, event):
        return event.signups.count()

    class Meta:
        model = VolunteerOpportunity
        fields = ["id", "title", "description", "date", "location", "required_volunteers", "status", "coordinator", "coordinator_name", "signup_count", "created_at"]
        read_only_fields = ["id", "coordinator", "created_at", "coordinator_name", "signup_count"]


class VolunteerProfileSerializer(serializers.ModelSerializer):
    user_id = serializers.UUIDField(source="user.user_id", read_only=True)
    full_name = serializers.CharField(source="user.full_name", read_only=True)

    class Meta:
        model = VolunteerProfile
        fields = ["user_id", "full_name", "skills", "availability", "location", "blood_group", "supporting_certificates", "updated_at"]
        read_only_fields = ["user_id", "full_name", "updated_at"]


class VolunteerSignupSerializer(serializers.ModelSerializer):
    volunteer_name = serializers.CharField(source="volunteer.full_name", read_only=True)
    class Meta:
        model = VolunteerSignup
        fields = ["id", "volunteer", "volunteer_name", "event", "signed_up_at"]


class VolunteerAttendanceSerializer(serializers.ModelSerializer):
    volunteer_name = serializers.CharField(source="volunteer.full_name", read_only=True)
    class Meta:
        model = VolunteerAttendance
        fields = ["id", "volunteer", "volunteer_name", "event", "check_in_time", "check_out_time"]


class VolunteerMessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(source="sender.full_name", read_only=True)
    class Meta:
        model = VolunteerMessage
        fields = ["id", "sender", "sender_name", "event", "message", "timestamp"]
        read_only_fields = ["id", "sender", "sender_name", "timestamp"]


class VolunteerCertificateSerializer(serializers.ModelSerializer):
    volunteer_name = serializers.CharField(source="volunteer.full_name", read_only=True)
    event_name = serializers.CharField(source="event.title", read_only=True)
    coordinator_name = serializers.CharField(source="coordinator.full_name", read_only=True)
    organization = serializers.CharField(source="coordinator.full_name", read_only=True)
    class Meta:
        model = VolunteerCertificate
        fields = ["id", "volunteer", "volunteer_name", "event", "event_name", "completion_date", "coordinator", "coordinator_name", "organization", "issued_at"]
        read_only_fields = ["id", "coordinator", "issued_at", "volunteer_name", "event_name", "coordinator_name", "organization"]
