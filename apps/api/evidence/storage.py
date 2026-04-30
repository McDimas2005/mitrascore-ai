import uuid
from io import BytesIO
from pathlib import Path

from django.conf import settings
from django.utils.text import get_valid_filename

from audit.services import log_action

from .models import StorageBackend


class InMemoryEvidenceFile(BytesIO):
    def open(self, *args, **kwargs):
        self.seek(0)
        return self

    def close(self):
        self.seek(0)


def sanitize_upload_filename(filename):
    name = get_valid_filename(Path(filename or "uploaded-evidence").name)
    if not name or name in {".", ".."}:
        name = "uploaded-evidence"
    stem = Path(name).stem[:80] or "uploaded-evidence"
    suffix = Path(name).suffix.lower()[:12]
    return f"{stem}{suffix}"


def private_blob_name(profile_id, filename):
    return f"evidence/profile-{profile_id}/{uuid.uuid4().hex}-{sanitize_upload_filename(filename)}"


def azure_blob_enabled():
    return bool(
        settings.USE_AZURE_BLOB_STORAGE
        and settings.AZURE_STORAGE_CONNECTION_STRING
        and settings.AZURE_STORAGE_CONTAINER_NAME
    )


def storage_runtime_status():
    return {
        "storage_mode": "azure_blob" if azure_blob_enabled() else "local",
        "use_azure_blob_storage": bool(settings.USE_AZURE_BLOB_STORAGE),
        "azure_blob_configured": bool(settings.AZURE_STORAGE_CONNECTION_STRING and settings.AZURE_STORAGE_CONTAINER_NAME),
        "public_blob_urls_enabled": False,
    }


def store_uploaded_evidence(upload, profile, actor):
    safe_name = sanitize_upload_filename(getattr(upload, "name", "uploaded-evidence"))
    if not azure_blob_enabled():
        if settings.USE_AZURE_BLOB_STORAGE:
            log_action(
                actor,
                "BLOB_UPLOAD_FALLBACK_LOCAL",
                profile,
                {"reason": "Azure Blob env vars missing", "borrower_profile": profile.id, "filename": safe_name},
            )
        return StorageBackend.LOCAL, ""

    blob_name = private_blob_name(profile.id, safe_name)
    log_action(actor, "BLOB_UPLOAD_ATTEMPTED", profile, {"borrower_profile": profile.id, "blob_name": blob_name})
    try:
        from azure.storage.blob import ContentSettings
        from azure.storage.blob import BlobServiceClient
    except ImportError as exc:
        log_action(
            actor,
            "BLOB_UPLOAD_FAILED",
            profile,
            {"borrower_profile": profile.id, "blob_name": blob_name, "error": "azure-storage-blob package is not installed"},
        )
        return StorageBackend.LOCAL, ""

    try:
        upload.seek(0)
        service = BlobServiceClient.from_connection_string(settings.AZURE_STORAGE_CONNECTION_STRING)
        blob_client = service.get_blob_client(container=settings.AZURE_STORAGE_CONTAINER_NAME, blob=blob_name)
        blob_client.upload_blob(
            upload,
            overwrite=False,
            content_settings=ContentSettings(content_type=getattr(upload, "content_type", None)),
        )
        upload.seek(0)
    except Exception as exc:
        log_action(
            actor,
            "BLOB_UPLOAD_FAILED",
            profile,
            {"borrower_profile": profile.id, "blob_name": blob_name, "error": str(exc)[:500]},
        )
        return StorageBackend.LOCAL, ""

    log_action(actor, "BLOB_UPLOAD_SUCCEEDED", profile, {"borrower_profile": profile.id, "blob_name": blob_name, "container_private": True})
    return StorageBackend.AZURE_BLOB, blob_name


def evidence_file_for_processing(evidence_item):
    if evidence_item.storage_backend == StorageBackend.AZURE_BLOB and evidence_item.storage_reference and azure_blob_enabled():
        try:
            from azure.storage.blob import BlobServiceClient
        except ImportError as exc:
            raise RuntimeError("azure-storage-blob package is not installed") from exc
        service = BlobServiceClient.from_connection_string(settings.AZURE_STORAGE_CONNECTION_STRING)
        blob_client = service.get_blob_client(
            container=settings.AZURE_STORAGE_CONTAINER_NAME,
            blob=evidence_item.storage_reference,
        )
        data = blob_client.download_blob().readall()
        return InMemoryEvidenceFile(data)
    return evidence_item.file
