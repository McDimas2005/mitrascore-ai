from django.contrib import admin

from .models import CreditReadinessReview, InstantEvidenceCheck


@admin.register(InstantEvidenceCheck)
class InstantEvidenceCheckAdmin(admin.ModelAdmin):
    list_display = ("borrower_profile", "data_completeness_score", "evidence_quality_score", "can_submit_to_analyst")


@admin.register(CreditReadinessReview)
class CreditReadinessReviewAdmin(admin.ModelAdmin):
    list_display = ("borrower_profile", "score", "readiness_band", "confidence_level", "final_human_decision")
