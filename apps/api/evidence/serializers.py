from rest_framework import serializers

from .models import AIExtractionResult, EvidenceItem, SourceType


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

    class Meta:
        model = EvidenceItem
        fields = (
            "id",
            "borrower_profile",
            "evidence_type",
            "source_type",
            "file",
            "original_filename",
            "mime_type",
            "file_size",
            "uploaded_by",
            "uploaded_by_email",
            "field_agent_note",
            "ai_status",
            "extraction_result",
            "created_at",
        )
        read_only_fields = ("borrower_profile", "original_filename", "mime_type", "file_size", "uploaded_by", "ai_status")


class EvidenceUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = EvidenceItem
        fields = ("id", "evidence_type", "source_type", "file", "field_agent_note")

    def validate_source_type(self, value):
        user = self.context["request"].user
        if value in {SourceType.AGENT_ASSISTED, SourceType.AGENT_VERIFIED} and user.role != "FIELD_AGENT":
            raise serializers.ValidationError("Only field agents can use agent evidence source types.")
        return value


class EvidenceSourceTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = EvidenceItem
        fields = ("source_type", "field_agent_note")

    def validate_source_type(self, value):
        user = self.context["request"].user
        if user.role != "FIELD_AGENT":
            raise serializers.ValidationError("Only field agents can change evidence source type.")
        return value
