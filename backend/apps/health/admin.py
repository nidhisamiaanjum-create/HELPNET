from django.contrib import admin

from .models import HealthProfessional, HealthQuestion, HealthReply


@admin.register(HealthQuestion)
class HealthQuestionAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "author", "created_at")
    search_fields = ("title", "description", "author__full_name")


@admin.register(HealthReply)
class HealthReplyAdmin(admin.ModelAdmin):
    list_display = ("question", "author", "created_at")


@admin.register(HealthProfessional)
class HealthProfessionalAdmin(admin.ModelAdmin):
    list_display = ("name", "profession", "specialization", "verification_status")
    list_filter = ("verification_status",)
    search_fields = ("name", "profession", "specialization")
