from rest_framework import serializers

from accounts.serializers import UserSerializer
from audit.models import AuditLog
from evidence.serializers import EvidenceItemSerializer
from scoring.serializers import CreditReadinessReviewSerializer, InstantEvidenceCheckSerializer
from scoring.services import verification_readiness

from .models import BorrowerProfile, ConsentRecord
from .workflow import STATUS_LABELS, role_next_actions, workflow_stage


class ConsentRecordSerializer(serializers.ModelSerializer):
    given_by_email = serializers.EmailField(source="given_by.email", read_only=True)

    class Meta:
        model = ConsentRecord
        fields = (
            "id",
            "borrower_profile",
            "consent_given",
            "consent_version",
            "consent_text_snapshot",
            "data_processing_purpose",
            "ai_usage_disclosure",
            "user_rights_disclosure",
            "given_by",
            "given_by_email",
            "given_at",
        )
        read_only_fields = ("borrower_profile", "given_by", "given_at")


class ConsentCreateSerializer(serializers.Serializer):
    consent_given = serializers.BooleanField()


class BorrowerProfileSerializer(serializers.ModelSerializer):
    owner_detail = UserSerializer(source="owner", read_only=True)
    created_by_detail = UserSerializer(source="created_by", read_only=True)
    assisted_by_detail = UserSerializer(source="assisted_by", read_only=True)
    consent = ConsentRecordSerializer(read_only=True)
    latest_instant_check = serializers.SerializerMethodField()
    latest_review = serializers.SerializerMethodField()
    status_label = serializers.SerializerMethodField()
    workflow_stage = serializers.SerializerMethodField()
    role_next_actions = serializers.SerializerMethodField()
    verification_readiness = serializers.SerializerMethodField()
    evidence_count = serializers.IntegerField(source="evidence_items.count", read_only=True)

    class Meta:
        model = BorrowerProfile
        fields = (
            "id",
            "owner",
            "owner_detail",
            "business_name",
            "business_category",
            "business_duration_months",
            "financing_purpose",
            "requested_amount",
            "estimated_monthly_revenue",
            "estimated_monthly_expense",
            "simple_cashflow_note",
            "business_note",
            "status",
            "status_label",
            "workflow_stage",
            "role_next_actions",
            "verification_readiness",
            "created_by",
            "created_by_detail",
            "assisted_by",
            "assisted_by_detail",
            "consent",
            "latest_instant_check",
            "latest_review",
            "evidence_count",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("status", "created_by", "assisted_by")

    def get_latest_instant_check(self, obj):
        check = obj.instant_checks.first()
        return InstantEvidenceCheckSerializer(check).data if check else None

    def get_latest_review(self, obj):
        review = obj.reviews.first()
        return CreditReadinessReviewSerializer(review).data if review else None

    def get_status_label(self, obj):
        return STATUS_LABELS.get(obj.status, obj.get_status_display())

    def get_workflow_stage(self, obj):
        return workflow_stage(obj)

    def get_role_next_actions(self, obj):
        return role_next_actions(obj)

    def get_verification_readiness(self, obj):
        return verification_readiness(obj)


class BorrowerCaseDetailSerializer(BorrowerProfileSerializer):
    evidence_items = EvidenceItemSerializer(many=True, read_only=True)
    instant_checks = InstantEvidenceCheckSerializer(many=True, read_only=True)
    reviews = CreditReadinessReviewSerializer(many=True, read_only=True)

    class Meta(BorrowerProfileSerializer.Meta):
        fields = BorrowerProfileSerializer.Meta.fields + ("evidence_items", "instant_checks", "reviews")


class AuditLogSerializer(serializers.ModelSerializer):
    actor_email = serializers.EmailField(source="actor.email", read_only=True)

    class Meta:
        model = AuditLog
        fields = ("id", "actor", "actor_email", "action", "entity_type", "entity_id", "metadata", "created_at")
