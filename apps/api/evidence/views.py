from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import UserRole
from ai_services.services import process_evidence_item
from audit.services import log_action
from borrowers.models import BorrowerProfile, BorrowerStatus
from borrowers.permissions import can_access_profile
from borrowers.workflow import is_final_locked
from scoring.services import require_consent

from .models import EvidenceItem, SourceType, StorageBackend
from .serializers import EvidenceItemSerializer, EvidenceSourceTypeSerializer, EvidenceUploadSerializer
from .storage import sanitize_upload_filename, store_uploaded_evidence


FINAL_LOCKED_MESSAGE = (
    "Pengajuan ini sudah ditutup oleh keputusan review manusia. "
    "Bukti pada siklus ini tidak dapat diubah, ditambah, diproses ulang, atau dihapus oleh owner/field agent."
)


class EvidenceListCreateView(APIView):
    def get_profile(self, request, pk):
        profile = get_object_or_404(BorrowerProfile, pk=pk)
        if not can_access_profile(request.user, profile):
            raise PermissionDenied("You cannot access this borrower profile.")
        return profile

    def get(self, request, pk):
        profile = self.get_profile(request, pk)
        return Response(EvidenceItemSerializer(profile.evidence_items.all(), many=True, context={"request": request}).data)

    def post(self, request, pk):
        profile = self.get_profile(request, pk)
        if request.user.role == UserRole.ANALYST:
            raise PermissionDenied("Analysts can review submitted cases but cannot upload evidence.")
        if is_final_locked(profile) and request.user.role != UserRole.ADMIN:
            raise PermissionDenied(FINAL_LOCKED_MESSAGE)
        try:
            require_consent(profile)
        except PermissionError as exc:
            raise PermissionDenied(str(exc))
        serializer = EvidenceUploadSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        upload = serializer.validated_data["file"]
        safe_filename = sanitize_upload_filename(getattr(upload, "name", "uploaded-evidence"))
        storage_backend, storage_reference = store_uploaded_evidence(upload, profile, request.user)
        item_kwargs = {
            "borrower_profile": profile,
            "uploaded_by": request.user,
            "original_filename": safe_filename,
            "mime_type": getattr(upload, "content_type", ""),
            "file_size": getattr(upload, "size", 0) or 0,
            "storage_backend": storage_backend,
            "storage_reference": storage_reference,
        }
        if storage_backend == StorageBackend.AZURE_BLOB:
            item = EvidenceItem.objects.create(
                evidence_type=serializer.validated_data["evidence_type"],
                source_type=serializer.validated_data.get("source_type", SourceType.SELF_UPLOADED),
                field_agent_note=serializer.validated_data.get("field_agent_note", ""),
                file="",
                **item_kwargs,
            )
        else:
            item = serializer.save(**item_kwargs)
        if profile.status in {BorrowerStatus.CONSENTED, BorrowerStatus.DRAFT}:
            profile.status = BorrowerStatus.EVIDENCE_UPLOADED
            profile.save(update_fields=["status", "updated_at"])
        log_action(request.user, "EVIDENCE_UPLOADED", item, {"borrower_profile": profile.id, "source_type": item.source_type})
        return Response(EvidenceItemSerializer(item, context={"request": request}).data, status=status.HTTP_201_CREATED)


class EvidenceSourceTypeView(APIView):
    def patch(self, request, pk):
        item = get_object_or_404(EvidenceItem, pk=pk)
        if request.user.role != UserRole.FIELD_AGENT:
            raise PermissionDenied("Only field agents can update source type.")
        if not can_access_profile(request.user, item.borrower_profile):
            raise PermissionDenied("You cannot access this borrower profile.")
        if is_final_locked(item.borrower_profile):
            raise PermissionDenied(FINAL_LOCKED_MESSAGE)
        serializer = EvidenceSourceTypeSerializer(item, data=request.data, partial=True, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        log_action(
            request.user,
            "EVIDENCE_SOURCE_UPDATED",
            item,
            {"borrower_profile": item.borrower_profile_id, **serializer.validated_data},
        )
        return Response(EvidenceItemSerializer(item, context={"request": request}).data)


class EvidenceProcessView(APIView):
    def post(self, request, pk):
        item = get_object_or_404(EvidenceItem, pk=pk)
        if not can_access_profile(request.user, item.borrower_profile):
            raise PermissionDenied("You cannot access this borrower profile.")
        if request.user.role == UserRole.ANALYST:
            raise PermissionDenied("Analysts can review submitted cases but cannot process evidence.")
        if is_final_locked(item.borrower_profile) and request.user.role != UserRole.ADMIN:
            raise PermissionDenied(FINAL_LOCKED_MESSAGE)
        try:
            require_consent(item.borrower_profile)
        except PermissionError as exc:
            raise PermissionDenied(str(exc))
        result = process_evidence_item(item, actor=request.user)
        log_action(
            request.user,
            "EVIDENCE_PROCESSED",
            item,
            {"confidence_score": result.confidence_score, "ai_status": item.ai_status, "service_name": result.service_name},
        )
        return Response(EvidenceItemSerializer(item, context={"request": request}).data)


class EvidenceDetailView(APIView):
    def delete(self, request, pk):
        item = get_object_or_404(EvidenceItem, pk=pk)
        if not can_access_profile(request.user, item.borrower_profile):
            raise PermissionDenied("You cannot access this borrower profile.")
        if is_final_locked(item.borrower_profile) and request.user.role != UserRole.ADMIN:
            raise PermissionDenied(FINAL_LOCKED_MESSAGE)
        if item.borrower_profile.reviews.exists() and request.user.role != UserRole.ADMIN:
            raise PermissionDenied("Evidence from reviewed cases can only be deleted by admin in this local demo.")
        metadata = {
            "borrower_profile": item.borrower_profile_id,
            "original_filename": item.original_filename,
            "evidence_type": item.evidence_type,
            "source_type": item.source_type,
        }
        log_action(request.user, "EVIDENCE_DELETED", item, metadata)
        item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
