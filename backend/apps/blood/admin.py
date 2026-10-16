
from django.contrib import admin
from .models import DonorProfile, BloodRequest, DonationHistory


@admin.register(DonorProfile)
class DonorProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "blood_group",
        "area",
        "availability",
        "created_at",
    )
    search_fields = (
        "user__full_name",
        "user__email",
        "area",
    )
    list_filter = (
        "blood_group",
        "availability",
        "area",
    )


@admin.register(BloodRequest)
class BloodRequestAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "requester",
        "blood_group",
        "area",
        "hospital",
        "status",
        "created_at",
    )
    search_fields = (
        "requester__full_name",
        "area",
        "hospital",
        "details",
    )
    list_filter = (
        "blood_group",
        "status",
        "area",
        "created_at",
    )
    readonly_fields = ("created_at", "updated_at")


@admin.register(DonationHistory)
class DonationHistoryAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "donor",
        "blood_request",
        "donated_at",
    )
    search_fields = (
        "donor__full_name",
        "blood_request__area",
        "blood_request__hospital",
    )
    list_filter = ("donated_at",)
    readonly_fields = ("donated_at",)
