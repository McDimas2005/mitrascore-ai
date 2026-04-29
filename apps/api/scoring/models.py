from django.conf import settings
from django.db import models
from django.utils import timezone


class ReadinessBand(models.TextChoices):
    LOW = "LOW", "Low"
    MODERATE = "MODERATE", "Moderate"
    PROMISING = "PROMISING", "Promising"
    STRONG = "STRONG", "Strong"


class ConfidenceLevel(models.TextChoices):
    LOW = "LOW", "Low"
    MEDIUM = "MEDIUM", "Medium"
    HIGH = "HIGH", "High"


class HumanDecision(models.TextChoices):
    PENDING = "PENDING", "Pending"
    NEEDS_MORE_DATA = "NEEDS_MORE_DATA", "Needs More Data"
    RECOMMENDED_FOR_REVIEW = "RECOMMENDED_FOR_REVIEW", "Recommended For Review"
    NOT_RECOMMENDED_AT_THIS_STAGE = "NOT_RECOMMENDED_AT_THIS_STAGE", "Not Recommended At This Stage"
    APPROVED_FOR_FINANCING = "APPROVED_FOR_FINANCING", "Approved For Financing"
    DECLINED = "DECLINED", "Declined"


class InstantEvidenceCheck(models.Model):
    borrower_profile = models.ForeignKey("borrowers.BorrowerProfile", related_name="instant_checks", on_delete=models.CASCADE)
    data_completeness_score = models.PositiveIntegerField(default=0)
    evidence_quality_score = models.PositiveIntegerField(default=0)
    detected_business_indicators = models.JSONField(default=dict, blank=True)
    ocr_summary = models.TextField(blank=True)
    business_note_summary = models.TextField(blank=True)
    missing_data = models.JSONField(default=list, blank=True)
    weak_evidence = models.JSONField(default=list, blank=True)
    recommended_next_steps = models.JSONField(default=list, blank=True)
    can_submit_to_analyst = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ("-created_at",)


class CreditReadinessReview(models.Model):
    borrower_profile = models.ForeignKey("borrowers.BorrowerProfile", related_name="reviews", on_delete=models.CASCADE)
    score = models.PositiveIntegerField(default=0)
    readiness_band = models.CharField(max_length=20, choices=ReadinessBand.choices)
    confidence_level = models.CharField(max_length=20, choices=ConfidenceLevel.choices)
    positive_signals = models.JSONField(default=list, blank=True)
    red_flags = models.JSONField(default=list, blank=True)
    main_reasons = models.JSONField(default=list, blank=True)
    suggested_next_action = models.TextField(blank=True)
    score_breakdown = models.JSONField(default=dict, blank=True)
    analyst_notes = models.TextField(blank=True)
    final_human_decision = models.CharField(max_length=40, choices=HumanDecision.choices, default=HumanDecision.PENDING)
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ("-created_at",)
