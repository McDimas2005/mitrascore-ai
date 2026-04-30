from django.conf import settings
from django.db import models
from django.utils import timezone


class BorrowerStatus(models.TextChoices):
    DRAFT = "DRAFT", "Draft"
    CONSENTED = "CONSENTED", "Consented"
    EVIDENCE_UPLOADED = "EVIDENCE_UPLOADED", "Evidence Uploaded"
    NEEDS_COMPLETION = "NEEDS_COMPLETION", "Needs Completion"
    READY_FOR_ANALYST = "READY_FOR_ANALYST", "Ready for Analyst"
    UNDER_REVIEW = "UNDER_REVIEW", "Under Review"
    REVIEWED = "REVIEWED", "Reviewed"


class BorrowerProfile(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="owned_profiles", on_delete=models.CASCADE)
    business_name = models.CharField(max_length=255)
    business_category = models.CharField(max_length=120, blank=True)
    business_duration_months = models.PositiveIntegerField(default=0)
    financing_purpose = models.TextField(blank=True)
    requested_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    estimated_monthly_revenue = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    estimated_monthly_expense = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    simple_cashflow_note = models.TextField(blank=True)
    business_note = models.TextField(blank=True)
    status = models.CharField(max_length=32, choices=BorrowerStatus.choices, default=BorrowerStatus.DRAFT)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="created_profiles", null=True, on_delete=models.SET_NULL)
    assisted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="assisted_profiles", null=True, blank=True, on_delete=models.SET_NULL
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-updated_at",)

    def __str__(self):
        return self.business_name


class ConsentRecord(models.Model):
    borrower_profile = models.OneToOneField(BorrowerProfile, related_name="consent", on_delete=models.CASCADE)
    consent_given = models.BooleanField(default=False)
    consent_version = models.CharField(max_length=40, default="v1-local-demo")
    consent_text_snapshot = models.TextField()
    data_processing_purpose = models.TextField()
    ai_usage_disclosure = models.TextField()
    user_rights_disclosure = models.TextField()
    given_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    given_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Consent {self.borrower_profile_id}: {self.consent_given}"
