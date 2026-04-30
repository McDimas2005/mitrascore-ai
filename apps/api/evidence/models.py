from django.conf import settings
from django.db import models
from django.utils import timezone


class EvidenceType(models.TextChoices):
    BUSINESS_PHOTO = "BUSINESS_PHOTO", "Business Photo"
    RECEIPT = "RECEIPT", "Receipt"
    INVOICE = "INVOICE", "Invoice"
    SUPPLIER_NOTE = "SUPPLIER_NOTE", "Supplier Note"
    SALES_NOTE = "SALES_NOTE", "Sales Note"
    QRIS_SCREENSHOT = "QRIS_SCREENSHOT", "QRIS Screenshot"
    OTHER = "OTHER", "Other"


class SourceType(models.TextChoices):
    SELF_UPLOADED = "SELF_UPLOADED", "Self Uploaded"
    AGENT_ASSISTED = "AGENT_ASSISTED", "Agent Assisted"
    AGENT_VERIFIED = "AGENT_VERIFIED", "Agent Verified"


class AIStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    PROCESSED = "PROCESSED", "Processed"
    FAILED = "FAILED", "Failed"
    SKIPPED = "SKIPPED", "Skipped"


class EvidenceItem(models.Model):
    borrower_profile = models.ForeignKey("borrowers.BorrowerProfile", related_name="evidence_items", on_delete=models.CASCADE)
    evidence_type = models.CharField(max_length=32, choices=EvidenceType.choices)
    source_type = models.CharField(max_length=32, choices=SourceType.choices, default=SourceType.SELF_UPLOADED)
    file = models.FileField(upload_to="evidence/")
    original_filename = models.CharField(max_length=255)
    mime_type = models.CharField(max_length=120, blank=True)
    file_size = models.PositiveIntegerField(default=0)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    field_agent_note = models.TextField(blank=True)
    ai_status = models.CharField(max_length=20, choices=AIStatus.choices, default=AIStatus.PENDING)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return self.original_filename


class AIExtractionResult(models.Model):
    evidence_item = models.OneToOneField(EvidenceItem, related_name="extraction_result", on_delete=models.CASCADE)
    service_name = models.CharField(max_length=120)
    extracted_text = models.TextField(blank=True)
    extracted_fields = models.JSONField(default=dict, blank=True)
    detected_business_indicators = models.JSONField(default=dict, blank=True)
    confidence_score = models.FloatField(default=0)
    quality_flags = models.JSONField(default=list, blank=True)
    raw_response = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.service_name} result for {self.evidence_item_id}"
