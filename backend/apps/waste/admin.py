
from django.contrib import admin
from .models import (
    WasteCollector,
    WasteCollectorRating,
    WastePickupRequest,
)


@admin.register(WasteCollector)
class WasteCollectorAdmin(admin.ModelAdmin):
    list_display = ("name", "phone", "area", "shared_by", "created_at")
    search_fields = ("name", "phone", "area")
    list_filter = ("area", "created_at")


@admin.register(WasteCollectorRating)
class WasteCollectorRatingAdmin(admin.ModelAdmin):
    list_display = ("collector", "user", "rating", "created_at")
    list_filter = ("rating", "created_at")


@admin.register(WastePickupRequest)
class WastePickupRequestAdmin(admin.ModelAdmin):
    list_display = ("requester", "collector", "status", "created_at")
    list_filter = ("status", "created_at")
