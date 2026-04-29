from rest_framework import serializers

from .models import AIExtractionResult, EvidenceItem, SourceType


SOURCE_TYPE_DETAILS = {
    SourceType.SELF_UPLOADED: {
        "label": "Self uploaded",
        "summary": "Owner uploaded this evidence without field-agent handling.",
        "effect": "Counts as owner-provided evidence. It supports completeness and OCR extraction, but receives no field verification bonus.",
    },
    SourceType.AGENT_ASSISTED: {
        "label": "Agent assisted",
        "summary": "Field agent helped capture or upload the evidence for the owner.",
        "effect": "Shows assisted collection and improves audit context, but it is not a verification claim and receives no verification bonus.",
    },
    SourceType.AGENT_VERIFIED: {
        "label": "Agent verified",
        "summary": "Field agent reviewed the evidence against observed business context or original documents.",
        "effect": "Adds +4 evidence-quality points per verified item before the quality cap, which can improve Instant Evidence Check and DeepScore.",
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
            "uploaded_by",
            "uploaded_by_email",
            "field_agent_note",
            "ai_status",
            "extraction_result",
            "created_at",
        )
        read_only_fields = ("borrower_profile", "original_filename", "mime_type", "file_size", "uploaded_by", "ai_status")

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
            raise serializers.ValidationError("Only field agents can use agent evidence source types.")
        return value

    def validate(self, attrs):
        if attrs.get("source_type") == SourceType.AGENT_VERIFIED and not attrs.get("field_agent_note", "").strip():
            raise serializers.ValidationError({"field_agent_note": "Verification note is required for agent-verified evidence."})
        return attrs


class EvidenceSourceTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = EvidenceItem
        fields = ("source_type", "field_agent_note")

    def validate_source_type(self, value):
        user = self.context["request"].user
        if user.role != "FIELD_AGENT":
            raise serializers.ValidationError("Only field agents can change evidence source type.")
        return value

    def validate(self, attrs):
        source_type = attrs.get("source_type", self.instance.source_type if self.instance else None)
        note = attrs.get("field_agent_note", self.instance.field_agent_note if self.instance else "")
        if source_type == SourceType.AGENT_VERIFIED and not note.strip():
            raise serializers.ValidationError({"field_agent_note": "Verification note is required for agent-verified evidence."})
        return attrs
