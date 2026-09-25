from django.contrib import admin
from .models import GoodsInterest, GoodsListing, GoodsReport


@admin.register(GoodsListing)
class GoodsListingAdmin(admin.ModelAdmin):
    list_display = ("title", "seller", "condition", "asking_price", "location", "status", "created_at")
    list_filter = ("status", "condition")
    search_fields = ("title", "description", "location", "seller__full_name")


admin.site.register([GoodsInterest, GoodsReport])
