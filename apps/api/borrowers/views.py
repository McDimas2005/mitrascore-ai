from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import User, UserRole
from ai_services.services import ai_runtime_status
from audit.models import AuditLog
from audit.services import log_action
from scoring.models import CreditReadinessReview, HumanDecision
from scoring.serializers import CreditReadinessReviewSerializer, InstantEvidenceCheckSerializer
from scoring.services import require_consent, run_deepscore, run_instant_check, verification_readiness

from .models import BorrowerProfile, BorrowerStatus, ConsentRecord
from .permissions import can_access_profile
from .serializers import (
    AuditLogSerializer,
    BorrowerCaseDetailSerializer,
    BorrowerProfileSerializer,
    ConsentCreateSerializer,
    ConsentRecordSerializer,
)
from .workflow import RECOVERABLE_REVIEW_DECISIONS, is_final_locked, latest_decision


CONSENT_TEXT = (
    "Saya setuju data usaha dan bukti yang saya berikan diproses untuk menilai kesiapan kredit. "
    "AI hanya membantu analisis dan tidak menyetujui atau menolak pembiayaan."
)


FINAL_LOCKED_MESSAGE = (
    "Pengajuan ini sudah ditutup oleh keputusan review manusia. "
    "Perubahan, unggah bukti, check ulang, dan kirim ulang tidak tersedia untuk siklus yang sama."
)

ANALYST_REVIEW_STATUSES = {BorrowerStatus.READY_FOR_ANALYST, BorrowerStatus.UNDER_REVIEW, BorrowerStatus.REVIEWED}


def require_analyst_reviewable(profile, user=None):
    if user and user.role == UserRole.ADMIN:
        return
    if profile.status not in ANALYST_REVIEW_STATUSES and not profile.reviews.exists():
        raise PermissionDenied("Analysts can only review cases that have been submitted to the analyst queue.")


def first_active_field_agent():
    agent = User.objects.filter(role=UserRole.FIELD_AGENT, is_active=True).order_by("id").first()
    if not agent:
        raise ValidationError("No active field agent is available.")
    return agent


class BorrowerProfileListCreateView(APIView):
    def get(self, request):
        qs = BorrowerProfile.objects.select_related("owner", "created_by", "assisted_by").all()
        if request.user.role == UserRole.UMKM_OWNER:
            qs = qs.filter(owner=request.user)
        elif request.user.role == UserRole.FIELD_AGENT:
            qs = qs.filter(assisted_by=request.user) | qs.filter(created_by=request.user)
        elif request.user.role == UserRole.ANALYST:
            qs = qs.filter(status__in=ANALYST_REVIEW_STATUSES)
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


class RequestFieldAgentAssistView(APIView):
    def post(self, request):
        if request.user.role != UserRole.UMKM_OWNER:
            raise PermissionDenied("Only UMKM owners can request field agent assistance.")
        agent = first_active_field_agent()
        visit_info = {
            "store_address": request.data.get("store_address", "").strip(),
            "contact_phone": request.data.get("contact_phone", "").strip(),
            "preferred_visit_time": request.data.get("preferred_visit_time", "").strip(),
            "assistance_note": request.data.get("assistance_note", "").strip(),
        }
        profile_id = request.data.get("profile_id")
        profile = None
        if profile_id:
            profile = get_object_or_404(BorrowerProfile, pk=profile_id, owner=request.user)
            if latest_decision(profile) == HumanDecision.DECLINED:
                raise ValidationError(
                    "Pengajuan ini sudah ditolak dan ditutup. Minta bantuan agen melalui pengajuan baru atau kanal klarifikasi resmi."
                )
            if latest_decision(profile) and latest_decision(profile) not in RECOVERABLE_REVIEW_DECISIONS:
                raise ValidationError("Reviewed cases cannot request new field agent assistance.")
        if not profile:
            profile = (
                BorrowerProfile.objects.filter(
                    owner=request.user,
                    created_by=request.user,
                    assisted_by=agent,
                    status=BorrowerStatus.DRAFT,
                    business_name__startswith="Permintaan Bantuan Agen - ",
                )
                .order_by("-created_at")
                .first()
            )
        created = False
        if not profile:
            profile = BorrowerProfile.objects.create(
                owner=request.user,
                business_name=request.data.get("business_name") or f"Permintaan Bantuan Agen - {request.user.full_name}",
                business_category="",
                financing_purpose="Meminta bantuan field agent untuk melengkapi onboarding UMKM.",
                simple_cashflow_note="",
                business_note="",
                created_by=request.user,
                assisted_by=agent,
                status=BorrowerStatus.DRAFT,
            )
            created = True
        previous_note = profile.business_note.strip()
        visit_note = (
            "Permintaan bantuan agen:\n"
            f"- Alamat toko/lokasi: {visit_info['store_address'] or 'Belum diisi'}\n"
            f"- Kontak/WhatsApp: {visit_info['contact_phone'] or 'Belum diisi'}\n"
            f"- Waktu kunjungan yang diharapkan: {visit_info['preferred_visit_time'] or 'Belum diisi'}\n"
            f"- Kebutuhan bantuan: {visit_info['assistance_note'] or 'Membutuhkan bantuan untuk melengkapi profil dan bukti usaha.'}"
        )
        if previous_note and "Permintaan bantuan agen:" not in previous_note:
            profile.business_note = f"{visit_note}\n\nCatatan usaha sebelumnya:\n{previous_note}"
        else:
            profile.business_note = visit_note
        profile.assisted_by = agent
        profile.save(update_fields=["business_note", "assisted_by", "updated_at"])
        log_action(
            request.user,
            "FIELD_AGENT_ASSISTANCE_REQUESTED",
            profile,
            {"assisted_by": agent.id, "assisted_by_email": agent.email, "created": created, **visit_info},
        )
        return Response(BorrowerProfileSerializer(profile).data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


class BorrowerProfileDetailView(APIView):
    def get_object(self, request, pk):
        profile = get_object_or_404(BorrowerProfile, pk=pk)
        if not can_access_profile(request.user, profile):
            raise PermissionDenied("You cannot access this borrower profile.")
        if request.user.role == UserRole.ANALYST:
            require_analyst_reviewable(profile, request.user)
        return profile

    def get(self, request, pk):
        return Response(BorrowerCaseDetailSerializer(self.get_object(request, pk), context={"request": request}).data)

    def patch(self, request, pk):
        profile = self.get_object(request, pk)
        if is_final_locked(profile) and request.user.role != UserRole.ADMIN:
            raise PermissionDenied(FINAL_LOCKED_MESSAGE)
        serializer = BorrowerProfileSerializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        log_action(request.user, "BORROWER_PROFILE_UPDATED", profile, {"fields": list(serializer.validated_data.keys())})
        return Response(BorrowerProfileSerializer(profile).data)

    def delete(self, request, pk):
        profile = self.get_object(request, pk)
        if profile.reviews.exists() and request.user.role != UserRole.ADMIN:
            raise PermissionDenied("Reviewed cases can only be deleted by admin in this local demo.")
        if request.user.role == UserRole.ANALYST:
            raise PermissionDenied("Analysts cannot delete borrower profiles.")
        metadata = {"business_name": profile.business_name, "status": profile.status}
        log_action(request.user, "BORROWER_PROFILE_DELETED", profile, metadata)
        profile.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


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
                "ai_usage_disclosure": (
                    f"Mode AI aktif: {ai_runtime_status()['ai_mode']}. AI digunakan untuk OCR/ekstraksi bukti "
                    "dan skor berbasis aturan. AI tidak membuat keputusan pembiayaan."
                ),
                "user_rights_disclosure": "Pengguna dapat meminta koreksi data dan tinjauan manusia atas hasil analisis.",
                "given_by": request.user,
            },
        )
        if consent.consent_given:
            profile.status = BorrowerStatus.CONSENTED
            profile.save(update_fields=["status", "updated_at"])
        else:
            profile.status = BorrowerStatus.DRAFT
            profile.save(update_fields=["status", "updated_at"])
        log_action(request.user, "CONSENT_RECORDED", profile, {"consent_given": consent.consent_given})
        return Response(ConsentRecordSerializer(consent).data, status=status.HTTP_201_CREATED)


class InstantCheckRunView(APIView):
    def post(self, request, pk):
        profile = get_object_or_404(BorrowerProfile, pk=pk)
        if not can_access_profile(request.user, profile):
            raise PermissionDenied("You cannot access this borrower profile.")
        if is_final_locked(profile) and request.user.role != UserRole.ADMIN:
            raise PermissionDenied(FINAL_LOCKED_MESSAGE)
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
        if is_final_locked(profile):
            raise ValidationError(FINAL_LOCKED_MESSAGE)
        try:
            require_consent(profile)
        except PermissionError as exc:
            raise PermissionDenied(str(exc))
        check = profile.instant_checks.first()
        if not check or not check.can_submit_to_analyst:
            raise ValidationError("Run a sufficient Instant Evidence Check before submitting.")
        latest_review = profile.reviews.first()
        action = "SUBMITTED_TO_ANALYST"
        metadata = {}
        if latest_review:
            action = "RESPONSE_SUBMITTED_TO_ANALYST"
            metadata["responding_to_decision"] = latest_review.final_human_decision
        profile.status = BorrowerStatus.READY_FOR_ANALYST
        profile.save(update_fields=["status", "updated_at"])
        log_action(request.user, action, profile, metadata)
        return Response(BorrowerProfileSerializer(profile).data)


class UndoSubmitToAnalystView(APIView):
    def post(self, request, pk):
        profile = get_object_or_404(BorrowerProfile, pk=pk)
        if not can_access_profile(request.user, profile):
            raise PermissionDenied("You cannot access this borrower profile.")
        if profile.reviews.exists():
            raise ValidationError("Cannot undo submission after DeepScore Review has been created.")
        if profile.status not in {BorrowerStatus.READY_FOR_ANALYST, BorrowerStatus.UNDER_REVIEW}:
            raise ValidationError("Only submitted cases can be pulled back.")
        profile.status = BorrowerStatus.NEEDS_COMPLETION
        profile.save(update_fields=["status", "updated_at"])
        log_action(request.user, "SUBMISSION_UNDONE", profile, {})
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
        require_analyst_reviewable(profile, request.user)
        return Response(BorrowerCaseDetailSerializer(profile, context={"request": request}).data)


class DeepScoreView(APIView):
    def post(self, request, pk):
        if request.user.role not in {UserRole.ANALYST, UserRole.ADMIN}:
            raise PermissionDenied("Only analysts can run DeepScore Review.")
        profile = get_object_or_404(BorrowerProfile, pk=pk)
        require_analyst_reviewable(profile, request.user)
        try:
            review = run_deepscore(profile, request.user)
        except PermissionError as exc:
            raise PermissionDenied(str(exc))
        log_action(request.user, "DEEPSCORE_REVIEW_RUN", profile, {"score": review.score, "band": review.readiness_band})
        return Response(CreditReadinessReviewSerializer(review).data, status=status.HTTP_201_CREATED)


class AnalystFieldVerificationRequestView(APIView):
    def post(self, request, pk):
        if request.user.role not in {UserRole.ANALYST, UserRole.ADMIN}:
            raise PermissionDenied("Only analysts can request field verification.")
        profile = get_object_or_404(BorrowerProfile, pk=pk)
        require_analyst_reviewable(profile, request.user)
        if is_final_locked(profile) and request.user.role != UserRole.ADMIN:
            raise PermissionDenied(FINAL_LOCKED_MESSAGE)
        review = profile.reviews.first()
        if not review:
            raise ValidationError("Run DeepScore before requesting field-agent verification.")
        agent = profile.assisted_by or first_active_field_agent()
        readiness = verification_readiness(profile)
        note = request.data.get("analyst_notes", "").strip()
        missing = "; ".join(readiness["missing_requirements"])
        default_note = (
            "Minta field agent memverifikasi bukti kunci sebelum keputusan pembiayaan final. "
            f"Kekurangan: {missing or 'cek bukti keberadaan usaha dan bukti arus kas utama.'}"
        )
        review.final_human_decision = HumanDecision.NEEDS_MORE_DATA
        review.analyst_notes = note or default_note
        review.reviewed_by = request.user
        review.reviewed_at = timezone.now()
        review.save(update_fields=["final_human_decision", "analyst_notes", "reviewed_by", "reviewed_at"])
        profile.assisted_by = agent
        profile.status = BorrowerStatus.NEEDS_COMPLETION
        profile.save(update_fields=["assisted_by", "status", "updated_at"])
        log_action(
            request.user,
            "FIELD_AGENT_VERIFICATION_REQUESTED",
            profile,
            {
                "assisted_by": agent.id,
                "assisted_by_email": agent.email,
                "review": review.id,
                "verification_readiness": readiness,
            },
        )
        log_action(
            request.user,
            "HUMAN_DECISION_UPDATED",
            review,
            {"decision": HumanDecision.NEEDS_MORE_DATA, "borrower_profile": profile.id, "reason": "field_agent_verification_requested"},
        )
        return Response(BorrowerCaseDetailSerializer(profile, context={"request": request}).data)


class ReviewDecisionView(APIView):
    def patch(self, request, pk):
        if request.user.role not in {UserRole.ANALYST, UserRole.ADMIN}:
            raise PermissionDenied("Only analysts can update human decision.")
        review = get_object_or_404(CreditReadinessReview, pk=pk)
        decision = request.data.get("final_human_decision")
        if decision not in HumanDecision.values:
            raise ValidationError("Invalid decision.")
        analyst_notes = request.data.get("analyst_notes", review.analyst_notes)
        if decision == HumanDecision.DECLINED and not analyst_notes.strip():
            raise ValidationError({"analyst_notes": "Alasan penolakan wajib diisi agar owner memahami keputusan final."})
        readiness = verification_readiness(review.borrower_profile)
        if decision == HumanDecision.APPROVED_FOR_FINANCING and not readiness["approval_ready"]:
            raise ValidationError(
                {
                    "detail": "Approval belum bisa disimpan: bukti kunci perlu diverifikasi agen sebelum persetujuan pembiayaan.",
                    "verification_readiness": readiness,
                }
            )
        review.final_human_decision = decision
        review.analyst_notes = analyst_notes
        review.reviewed_by = request.user
        review.reviewed_at = timezone.now()
        review.save(update_fields=["final_human_decision", "analyst_notes", "reviewed_by", "reviewed_at"])
        if decision == HumanDecision.PENDING:
            review.borrower_profile.status = BorrowerStatus.UNDER_REVIEW
        elif decision == HumanDecision.NEEDS_MORE_DATA:
            review.borrower_profile.status = BorrowerStatus.NEEDS_COMPLETION
        else:
            review.borrower_profile.status = BorrowerStatus.REVIEWED
        review.borrower_profile.save(update_fields=["status", "updated_at"])
        log_action(
            request.user,
            "HUMAN_DECISION_UPDATED",
            review,
            {"decision": decision, "borrower_profile": review.borrower_profile_id},
        )
        return Response(CreditReadinessReviewSerializer(review).data)


class BorrowerAuditLogView(APIView):
    def get(self, request, pk):
        profile = get_object_or_404(BorrowerProfile, pk=pk)
        if not can_access_profile(request.user, profile):
            raise PermissionDenied("You cannot access this borrower profile.")
        if request.user.role == UserRole.ANALYST:
            require_analyst_reviewable(profile, request.user)
        logs = AuditLog.objects.filter(entity_id=str(pk), entity_type="BorrowerProfile") | AuditLog.objects.filter(
            metadata__borrower_profile=pk
        )
        return Response(AuditLogSerializer(logs.order_by("-created_at"), many=True).data)
