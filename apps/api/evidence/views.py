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
from scoring.services import require_consent

from .models import EvidenceItem
from .serializers import EvidenceItemSerializer, EvidenceSourceTypeSerializer, EvidenceUploadSerializer


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
        try:
            require_consent(profile)
        except PermissionError as exc:
            raise PermissionDenied(str(exc))
        serializer = EvidenceUploadSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        upload = serializer.validated_data["file"]
        item = serializer.save(
            borrower_profile=profile,
            uploaded_by=request.user,
            original_filename=getattr(upload, "name", "uploaded-evidence"),
            mime_type=getattr(upload, "content_type", ""),
            file_size=getattr(upload, "size", 0) or 0,
        )
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
        serializer = EvidenceSourceTypeSerializer(item, data=request.data, partial=True, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        log_action(request.user, "EVIDENCE_SOURCE_UPDATED", item, serializer.validated_data)
        return Response(EvidenceItemSerializer(item, context={"request": request}).data)


class EvidenceProcessView(APIView):
    def post(self, request, pk):
        item = get_object_or_404(EvidenceItem, pk=pk)
        if not can_access_profile(request.user, item.borrower_profile):
            raise PermissionDenied("You cannot access this borrower profile.")
        try:
            require_consent(item.borrower_profile)
        except PermissionError as exc:
            raise PermissionDenied(str(exc))
        result = process_evidence_item(item)
        log_action(request.user, "EVIDENCE_PROCESSED", item, {"confidence_score": result.confidence_score})
        return Response(EvidenceItemSerializer(item, context={"request": request}).data)


class EvidenceDetailView(APIView):
    def delete(self, request, pk):
        item = get_object_or_404(EvidenceItem, pk=pk)
        if not can_access_profile(request.user, item.borrower_profile):
            raise PermissionDenied("You cannot access this borrower profile.")
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
