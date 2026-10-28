from django.contrib import admin

from .models import JobOffer


@admin.register(JobOffer)
class JobOfferAdmin(admin.ModelAdmin):
    list_display = (
        "id", "position_title", "assessment", "evaluator", "candidate",
        "created_by", "salary", "modality", "status", "created_at",
    )
    list_filter = ("status", "modality", "created_at")
    search_fields = (
        "position_title", "assessment__title",
        "evaluator__username", "candidate__username",
    )
    raw_id_fields = ("assessment", "evaluator", "candidate", "created_by", "parent")
    readonly_fields = ("created_at", "updated_at", "responded_at")
