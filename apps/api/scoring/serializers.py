from rest_framework import serializers

from .models import CreditReadinessReview, InstantEvidenceCheck


class InstantEvidenceCheckSerializer(serializers.ModelSerializer):
    class Meta:
        model = InstantEvidenceCheck
        fields = (
            "id",
            "borrower_profile",
            "data_completeness_score",
            "evidence_quality_score",
            "detected_business_indicators",
            "ocr_summary",
            "business_note_summary",
            "missing_data",
            "weak_evidence",
            "recommended_next_steps",
            "can_submit_to_analyst",
            "created_at",
        )


class CreditReadinessReviewSerializer(serializers.ModelSerializer):
    reviewed_by_email = serializers.EmailField(source="reviewed_by.email", read_only=True)

    class Meta:
        model = CreditReadinessReview
        fields = (
            "id",
            "borrower_profile",
            "score",
            "readiness_band",
            "confidence_level",
            "positive_signals",
            "red_flags",
            "main_reasons",
            "suggested_next_action",
            "score_breakdown",
            "analyst_notes",
            "final_human_decision",
            "reviewed_by",
            "reviewed_by_email",
            "reviewed_at",
            "created_at",
        )
        read_only_fields = ("score", "readiness_band", "confidence_level", "reviewed_by", "reviewed_at")
