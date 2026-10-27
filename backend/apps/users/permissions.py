from rest_framework.permissions import BasePermission
from .models import UserProfile

class IsAdminUserRole(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return (
            user.is_authenticated
            and user.is_superuser
        )


class IsCitizenUser(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == "Citizen"
        )


class IsNGOUser(BasePermission):
    def has_permission(self, request, view):
        user = request.user

        if not user or not user.is_authenticated:
            return False

        if user.is_superuser:
            return True

        if user.role != "NGO":
            return False

        return user.profiles.filter(
            profile_type=UserProfile.Type.NGO,
            ngo_approval_status=UserProfile.NGOApprovalStatus.APPROVED,
            status=UserProfile.Status.ACTIVE,
        ).exists()


class IsVolunteerUser(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == "Volunteer"
        )


class IsFarmerUser(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == "Farmer"
        )
