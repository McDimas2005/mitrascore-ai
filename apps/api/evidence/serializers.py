from pathlib import Path

from django.conf import settings
from rest_framework import serializers

from .models import AIExtractionResult, EvidenceItem, SourceType


SOURCE_TYPE_DETAILS = {
    SourceType.SELF_UPLOADED: {
        "label": "Unggahan owner",
        "summary": "Owner mengunggah bukti ini sendiri tanpa bantuan field agent.",
        "effect": "Dipakai untuk kelengkapan data dan OCR, tetapi belum mendapat bobot verifikasi lapangan.",
    },
    SourceType.AGENT_ASSISTED: {
        "label": "Dibantu agen",
        "summary": "Field agent membantu mengambil atau mengunggah bukti untuk owner.",
        "effect": "Mencatat pendampingan dan konteks audit, tetapi belum berarti bukti sudah diverifikasi.",
    },
    SourceType.AGENT_VERIFIED: {
        "label": "Diverifikasi agen",
        "summary": "Field agent mencocokkan bukti dengan konteks usaha yang dilihat atau dokumen asli.",
        "effect": "Menambah +4 poin kualitas bukti per item sebelum batas skor, dan dapat memperkuat Instant Evidence Check serta DeepScore.",
    },
}


class AIExtractionResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIExtractionResult
        fields = (
            "id",
            "service_name",
            "extracted_text",
            "extracted_fields",
            "detected_business_indicators",
            "confidence_score",
            "quality_flags",
            "raw_response",
            "created_at",
        )


class EvidenceItemSerializer(serializers.ModelSerializer):
    extraction_result = AIExtractionResultSerializer(read_only=True)
    uploaded_by_email = serializers.EmailField(source="uploaded_by.email", read_only=True)
    source_type_label = serializers.SerializerMethodField()
    source_type_summary = serializers.SerializerMethodField()
    source_type_effect = serializers.SerializerMethodField()

    class Meta:
        model = EvidenceItem
        fields = (
            "id",
            "borrower_profile",
            "evidence_type",
            "source_type",
            "source_type_label",
            "source_type_summary",
            "source_type_effect",
            "file",
            "original_filename",
            "mime_type",
            "file_size",
            "storage_backend",
            "storage_reference",
            "uploaded_by",
            "uploaded_by_email",
            "field_agent_note",
            "ai_status",
            "extraction_result",
            "created_at",
        )
        read_only_fields = (
            "borrower_profile",
            "original_filename",
            "mime_type",
            "file_size",
            "storage_backend",
            "storage_reference",
            "uploaded_by",
            "ai_status",
        )

    def get_source_type_label(self, obj):
        return SOURCE_TYPE_DETAILS.get(obj.source_type, {}).get("label", obj.get_source_type_display())

    def get_source_type_summary(self, obj):
        return SOURCE_TYPE_DETAILS.get(obj.source_type, {}).get("summary", "")

    def get_source_type_effect(self, obj):
        return SOURCE_TYPE_DETAILS.get(obj.source_type, {}).get("effect", "")


class EvidenceUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = EvidenceItem
        fields = ("id", "evidence_type", "source_type", "file", "field_agent_note")

    def validate_source_type(self, value):
        user = self.context["request"].user
        if value in {SourceType.AGENT_ASSISTED, SourceType.AGENT_VERIFIED} and user.role != "FIELD_AGENT":
            raise serializers.ValidationError("Hanya field agent yang dapat memakai status bukti berbasis agen.")
        return value

    def validate_file(self, upload):
        size = getattr(upload, "size", 0) or 0
        if size <= 0:
            raise serializers.ValidationError("File bukti tidak boleh kosong.")
        if size > settings.MAX_EVIDENCE_UPLOAD_BYTES:
            limit_mb = settings.MAX_EVIDENCE_UPLOAD_BYTES / (1024 * 1024)
            raise serializers.ValidationError(f"Ukuran file maksimal {limit_mb:.0f} MB untuk demo aman.")
        extension = Path(getattr(upload, "name", "")).suffix.lower().lstrip(".")
        if extension not in settings.ALLOWED_EVIDENCE_EXTENSIONS:
            allowed = ", ".join(sorted(settings.ALLOWED_EVIDENCE_EXTENSIONS))
            raise serializers.ValidationError(f"Tipe file tidak didukung. Gunakan: {allowed}.")
        content_type = (getattr(upload, "content_type", "") or "").lower()
        if content_type and content_type not in settings.ALLOWED_EVIDENCE_MIME_TYPES:
            allowed = ", ".join(sorted(settings.ALLOWED_EVIDENCE_MIME_TYPES))
            raise serializers.ValidationError(f"MIME type tidak didukung untuk demo aman. Gunakan: {allowed}.")
        return upload

    def validate(self, attrs):
        if attrs.get("source_type") == SourceType.AGENT_VERIFIED and not attrs.get("field_agent_note", "").strip():
            raise serializers.ValidationError({"field_agent_note": "Catatan verifikasi wajib untuk bukti yang diverifikasi agen."})
        return attrs


class EvidenceSourceTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = EvidenceItem
        fields = ("source_type", "field_agent_note")

    def validate_source_type(self, value):
        user = self.context["request"].user
        if user.role != "FIELD_AGENT":
            raise serializers.ValidationError("Hanya field agent yang dapat mengubah status sumber bukti.")
        return value

    def validate(self, attrs):
        source_type = attrs.get("source_type", self.instance.source_type if self.instance else None)
        note = attrs.get("field_agent_note", self.instance.field_agent_note if self.instance else "")
        if source_type == SourceType.AGENT_VERIFIED and not note.strip():
            raise serializers.ValidationError({"field_agent_note": "Catatan verifikasi wajib untuk bukti yang diverifikasi agen."})
        return attrs
