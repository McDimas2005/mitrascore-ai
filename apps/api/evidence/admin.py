from django.contrib import admin

from .models import AIExtractionResult, EvidenceItem


@admin.register(EvidenceItem)
class EvidenceItemAdmin(admin.ModelAdmin):
    list_display = ("original_filename", "borrower_profile", "evidence_type", "source_type", "ai_status")
    list_filter = ("evidence_type", "source_type", "ai_status")


@admin.register(AIExtractionResult)
class AIExtractionResultAdmin(admin.ModelAdmin):
    list_display = ("evidence_item", "service_name", "confidence_score", "created_at")
