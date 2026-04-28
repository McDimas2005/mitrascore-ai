from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import User, UserRole
from audit.models import AuditLog
from audit.services import log_action
from scoring.models import CreditReadinessReview, HumanDecision
from scoring.serializers import CreditReadinessReviewSerializer, InstantEvidenceCheckSerializer
from scoring.services import require_consent, run_deepscore, run_instant_check

from .models import BorrowerProfile, BorrowerStatus, ConsentRecord
from .permissions import can_access_profile
from .serializers import (
    AuditLogSerializer,
    BorrowerCaseDetailSerializer,
    BorrowerProfileSerializer,
    ConsentCreateSerializer,
    ConsentRecordSerializer,
)


CONSENT_TEXT = (
    "Saya setuju data usaha dan bukti yang saya berikan diproses untuk menilai kesiapan kredit. "
    "AI hanya membantu analisis dan tidak menyetujui atau menolak pembiayaan."
)


class BorrowerProfileListCreateView(APIView):
    def get(self, request):
        qs = BorrowerProfile.objects.select_related("owner", "created_by", "assisted_by").all()
        if request.user.role == UserRole.UMKM_OWNER:
            qs = qs.filter(owner=request.user)
        elif request.user.role == UserRole.FIELD_AGENT:
            qs = qs.filter(assisted_by=request.user) | qs.filter(created_by=request.user)
        return Response(BorrowerProfileSerializer(qs.distinct(), many=True).data)

    def post(self, request):
        payload = request.data.copy()
        if request.user.role == UserRole.UMKM_OWNER:
            payload["owner"] = request.user.id
        elif request.user.role == UserRole.FIELD_AGENT and not payload.get("owner"):
            owner = User.objects.filter(role=UserRole.UMKM_OWNER).first()
            if not owner:
                raise ValidationError("Create an UMKM owner user before assisted onboarding.")
            payload["owner"] = owner.id
        serializer = BorrowerProfileSerializer(data=payload)
        serializer.is_valid(raise_exception=True)
        profile = serializer.save(
            created_by=request.user,
            assisted_by=request.user if request.user.role == UserRole.FIELD_AGENT else None,
        )
        log_action(request.user, "BORROWER_PROFILE_CREATED", profile, {"status": profile.status})
        return Response(BorrowerProfileSerializer(profile).data, status=status.HTTP_201_CREATED)


class BorrowerProfileDetailView(APIView):
    def get_object(self, request, pk):
        profile = get_object_or_404(BorrowerProfile, pk=pk)
        if not can_access_profile(request.user, profile):
            raise PermissionDenied("You cannot access this borrower profile.")
        return profile

    def get(self, request, pk):
        return Response(BorrowerCaseDetailSerializer(self.get_object(request, pk), context={"request": request}).data)

    def patch(self, request, pk):
        profile = self.get_object(request, pk)
        serializer = BorrowerProfileSerializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        log_action(request.user, "BORROWER_PROFILE_UPDATED", profile, {"fields": list(serializer.validated_data.keys())})
        return Response(BorrowerProfileSerializer(profile).data)


class ConsentView(APIView):
    def get(self, request, pk):
        profile = get_object_or_404(BorrowerProfile, pk=pk)
        if not can_access_profile(request.user, profile):
            raise PermissionDenied("You cannot access this borrower profile.")
        if not hasattr(profile, "consent"):
            return Response({"detail": "Consent has not been recorded."}, status=status.HTTP_404_NOT_FOUND)
        return Response(ConsentRecordSerializer(profile.consent).data)

    def post(self, request, pk):
        profile = get_object_or_404(BorrowerProfile, pk=pk)
        if not can_access_profile(request.user, profile):
            raise PermissionDenied("You cannot access this borrower profile.")
        serializer = ConsentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        consent, _ = ConsentRecord.objects.update_or_create(
            borrower_profile=profile,
            defaults={
                "consent_given": serializer.validated_data["consent_given"],
                "consent_text_snapshot": CONSENT_TEXT,
                "data_processing_purpose": "Menilai kesiapan kredit UMKM berdasarkan profil dan bukti usaha yang diberikan.",
                "ai_usage_disclosure": "AI mock digunakan untuk OCR, ringkasan, dan skor berbasis aturan. AI tidak membuat keputusan pembiayaan.",
                "user_rights_disclosure": "Pengguna dapat meminta koreksi data dan tinjauan manusia atas hasil analisis.",
                "given_by": request.user,
            },
        )
        if consent.consent_given:
            profile.status = BorrowerStatus.CONSENTED
            profile.save(update_fields=["status", "updated_at"])
        log_action(request.user, "CONSENT_RECORDED", profile, {"consent_given": consent.consent_given})
        return Response(ConsentRecordSerializer(consent).data, status=status.HTTP_201_CREATED)


class InstantCheckRunView(APIView):
    def post(self, request, pk):
        profile = get_object_or_404(BorrowerProfile, pk=pk)
        if not can_access_profile(request.user, profile):
            raise PermissionDenied("You cannot access this borrower profile.")
        try:
            check = run_instant_check(profile)
        except PermissionError as exc:
            raise PermissionDenied(str(exc))
        log_action(request.user, "INSTANT_CHECK_RUN", profile, {"can_submit_to_analyst": check.can_submit_to_analyst})
        return Response(InstantEvidenceCheckSerializer(check).data, status=status.HTTP_201_CREATED)


class InstantCheckLatestView(APIView):
    def get(self, request, pk):
        profile = get_object_or_404(BorrowerProfile, pk=pk)
        if not can_access_profile(request.user, profile):
            raise PermissionDenied("You cannot access this borrower profile.")
        check = profile.instant_checks.first()
        if not check:
            return Response({"detail": "No instant check has been run."}, status=status.HTTP_404_NOT_FOUND)
        return Response(InstantEvidenceCheckSerializer(check).data)


class SubmitToAnalystView(APIView):
    def post(self, request, pk):
        profile = get_object_or_404(BorrowerProfile, pk=pk)
        if not can_access_profile(request.user, profile):
            raise PermissionDenied("You cannot access this borrower profile.")
        try:
            require_consent(profile)
        except PermissionError as exc:
            raise PermissionDenied(str(exc))
        check = profile.instant_checks.first()
        if not check or not check.can_submit_to_analyst:
            raise ValidationError("Run a sufficient Instant Evidence Check before submitting.")
        profile.status = BorrowerStatus.READY_FOR_ANALYST
        profile.save(update_fields=["status", "updated_at"])
        log_action(request.user, "SUBMITTED_TO_ANALYST", profile, {})
        return Response(BorrowerProfileSerializer(profile).data)


class AnalystCasesView(APIView):
    def get(self, request):
        if request.user.role not in {UserRole.ANALYST, UserRole.ADMIN}:
            raise PermissionDenied("Only analysts can view submitted cases.")
        qs = BorrowerProfile.objects.filter(status__in=[BorrowerStatus.READY_FOR_ANALYST, BorrowerStatus.UNDER_REVIEW, BorrowerStatus.REVIEWED])
        return Response(BorrowerProfileSerializer(qs, many=True).data)


class AnalystCaseDetailView(APIView):
    def get(self, request, pk):
        if request.user.role not in {UserRole.ANALYST, UserRole.ADMIN}:
            raise PermissionDenied("Only analysts can view submitted cases.")
        profile = get_object_or_404(BorrowerProfile, pk=pk)
        return Response(BorrowerCaseDetailSerializer(profile, context={"request": request}).data)


class DeepScoreView(APIView):
    def post(self, request, pk):
        if request.user.role not in {UserRole.ANALYST, UserRole.ADMIN}:
            raise PermissionDenied("Only analysts can run DeepScore Review.")
        profile = get_object_or_404(BorrowerProfile, pk=pk)
        try:
            review = run_deepscore(profile, request.user)
        except PermissionError as exc:
            raise PermissionDenied(str(exc))
        log_action(request.user, "DEEPSCORE_REVIEW_RUN", profile, {"score": review.score, "band": review.readiness_band})
        return Response(CreditReadinessReviewSerializer(review).data, status=status.HTTP_201_CREATED)


class ReviewDecisionView(APIView):
    def patch(self, request, pk):
        if request.user.role not in {UserRole.ANALYST, UserRole.ADMIN}:
            raise PermissionDenied("Only analysts can update human decision.")
        review = get_object_or_404(CreditReadinessReview, pk=pk)
        decision = request.data.get("final_human_decision")
        if decision not in HumanDecision.values:
            raise ValidationError("Invalid decision.")
        review.final_human_decision = decision
        review.analyst_notes = request.data.get("analyst_notes", review.analyst_notes)
        review.reviewed_by = request.user
        review.reviewed_at = timezone.now()
        review.save(update_fields=["final_human_decision", "analyst_notes", "reviewed_by", "reviewed_at"])
        log_action(request.user, "HUMAN_DECISION_UPDATED", review, {"decision": decision})
        return Response(CreditReadinessReviewSerializer(review).data)


class BorrowerAuditLogView(APIView):
    def get(self, request, pk):
        profile = get_object_or_404(BorrowerProfile, pk=pk)
        if not can_access_profile(request.user, profile):
            raise PermissionDenied("You cannot access this borrower profile.")
        logs = AuditLog.objects.filter(entity_id=str(pk), entity_type="BorrowerProfile") | AuditLog.objects.filter(
            metadata__borrower_profile=pk
        )
        return Response(AuditLogSerializer(logs.order_by("-created_at"), many=True).data)
