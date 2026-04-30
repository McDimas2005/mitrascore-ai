from django.conf import settings

from audit.services import log_action
from evidence.models import AIExtractionResult, AIStatus, EvidenceType

from .azure_clients import AzureAIClientError, AzureDocumentIntelligenceClient, AzureVisionClient
from .mock_clients import MockDocumentIntelligenceClient, MockLanguageClient, MockSearchClient, MockVisionClient


def use_mock_ai():
    return bool(getattr(settings, "USE_MOCK_AI", True))


def azure_vision_configured():
    return bool(settings.AZURE_AI_VISION_ENDPOINT and settings.AZURE_AI_VISION_KEY)


def azure_document_configured():
    return bool(settings.AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT and settings.AZURE_DOCUMENT_INTELLIGENCE_KEY)


def ai_runtime_status():
    return {
        "ai_mode": "mock" if use_mock_ai() else "azure",
        "use_mock_ai": use_mock_ai(),
        "azure_vision_configured": azure_vision_configured(),
        "azure_document_intelligence_configured": azure_document_configured(),
        "field_note_summary_mode": "mock",
        "evidence_search_mode": "mock",
        "responsible_ai_notice": "AI hanya mendukung analisis. Keputusan akhir pembiayaan tetap dilakukan oleh analis manusia.",
    }


def _failure_result(evidence_item, service_name, message):
    result, _ = AIExtractionResult.objects.update_or_create(
        evidence_item=evidence_item,
        defaults={
            "service_name": service_name,
            "extracted_text": message,
            "extracted_fields": {},
            "detected_business_indicators": {"indicators": []},
            "confidence_score": 0,
            "quality_flags": [message],
            "raw_response": {"error": message, "fallback_available": "Set USE_MOCK_AI=true for emergency demo fallback."},
        },
    )
    evidence_item.ai_status = AIStatus.FAILED
    evidence_item.save(update_fields=["ai_status"])
    return result


def _process_mock(evidence_item, actor=None):
    log_action(actor, "AI_MOCK_PROCESSING_STARTED", evidence_item, {"borrower_profile": evidence_item.borrower_profile_id})
    vision = MockVisionClient().analyze_image(evidence_item.original_filename, evidence_item.evidence_type)
    document = MockDocumentIntelligenceClient().extract_document(evidence_item.original_filename, evidence_item.evidence_type)
    indicators = list(dict.fromkeys(vision["indicators"] + document["indicators"]))
    flags = list(dict.fromkeys(vision["quality_flags"] + document["quality_flags"]))
    confidence = round((vision["confidence"] + document["confidence"]) / 2, 2)
    result, _ = AIExtractionResult.objects.update_or_create(
        evidence_item=evidence_item,
        defaults={
            "service_name": "MockVisionClient+MockDocumentIntelligenceClient",
            "extracted_text": document["extracted_text"],
            "extracted_fields": document["extracted_fields"],
            "detected_business_indicators": {"indicators": indicators},
            "confidence_score": confidence,
            "quality_flags": flags,
            "raw_response": {"vision": vision, "document": document},
        },
    )
    evidence_item.ai_status = AIStatus.PROCESSED
    evidence_item.save(update_fields=["ai_status"])
    log_action(
        actor,
        "AI_MOCK_PROCESSING_COMPLETED",
        evidence_item,
        {"borrower_profile": evidence_item.borrower_profile_id, "confidence_score": result.confidence_score},
    )
    return result


def _process_azure_vision(evidence_item, actor=None):
    log_action(actor, "AZURE_VISION_PROCESSING_STARTED", evidence_item, {"borrower_profile": evidence_item.borrower_profile_id})
    if not azure_vision_configured():
        message = "Azure AI Vision is not configured. Set AZURE_AI_VISION_ENDPOINT and AZURE_AI_VISION_KEY, or set USE_MOCK_AI=true."
        log_action(actor, "AI_PROCESSING_FAILED", evidence_item, {"borrower_profile": evidence_item.borrower_profile_id, "service": "AzureVisionClient", "error": message})
        return _failure_result(evidence_item, "AzureVisionClientUnavailable", message)
    client = AzureVisionClient(settings.AZURE_AI_VISION_ENDPOINT, settings.AZURE_AI_VISION_KEY)
    try:
        vision = client.analyze_image(evidence_item.file, evidence_item.original_filename, evidence_item.evidence_type, evidence_item.mime_type)
    except AzureAIClientError as exc:
        message = str(exc)
        log_action(actor, "AI_PROCESSING_FAILED", evidence_item, {"borrower_profile": evidence_item.borrower_profile_id, "service": client.service_name, "error": message})
        return _failure_result(evidence_item, client.service_name, message)
    result, _ = AIExtractionResult.objects.update_or_create(
        evidence_item=evidence_item,
        defaults={
            "service_name": client.service_name,
            "extracted_text": "\n".join(vision.get("signage_text", [])),
            "extracted_fields": {
                "possible_product_category": vision.get("possible_product_category", []),
                "inventory_stock_presence": vision.get("inventory_stock_presence", False),
                "storefront_business_context": vision.get("storefront_business_context", False),
                "business_context": vision.get("business_context", ""),
            },
            "detected_business_indicators": {"indicators": vision["indicators"]},
            "confidence_score": vision["confidence"],
            "quality_flags": vision["quality_flags"],
            "raw_response": {"vision": vision.get("raw_response", {}), "responsible_ai_constraints": "No face recognition or protected-attribute inference used."},
        },
    )
    evidence_item.ai_status = AIStatus.PROCESSED
    evidence_item.save(update_fields=["ai_status"])
    log_action(actor, "AZURE_VISION_PROCESSING_COMPLETED", evidence_item, {"borrower_profile": evidence_item.borrower_profile_id, "confidence_score": result.confidence_score})
    return result


def _process_azure_document(evidence_item, actor=None):
    log_action(actor, "AZURE_DOCUMENT_INTELLIGENCE_PROCESSING_STARTED", evidence_item, {"borrower_profile": evidence_item.borrower_profile_id})
    if not azure_document_configured():
        message = (
            "Azure Document Intelligence is not configured. Set "
            "AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT and AZURE_DOCUMENT_INTELLIGENCE_KEY, or set USE_MOCK_AI=true."
        )
        log_action(actor, "AI_PROCESSING_FAILED", evidence_item, {"borrower_profile": evidence_item.borrower_profile_id, "service": "AzureDocumentIntelligenceClient", "error": message})
        return _failure_result(evidence_item, "AzureDocumentIntelligenceClientUnavailable", message)
    client = AzureDocumentIntelligenceClient(settings.AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT, settings.AZURE_DOCUMENT_INTELLIGENCE_KEY)
    try:
        document = client.extract_document(evidence_item.file, evidence_item.original_filename, evidence_item.evidence_type, evidence_item.mime_type)
    except AzureAIClientError as exc:
        message = str(exc)
        log_action(actor, "AI_PROCESSING_FAILED", evidence_item, {"borrower_profile": evidence_item.borrower_profile_id, "service": client.service_name, "error": message})
        return _failure_result(evidence_item, client.service_name, message)
    result, _ = AIExtractionResult.objects.update_or_create(
        evidence_item=evidence_item,
        defaults={
            "service_name": client.service_name,
            "extracted_text": document["extracted_text"],
            "extracted_fields": document["extracted_fields"],
            "detected_business_indicators": {"indicators": document["indicators"]},
            "confidence_score": document["confidence"],
            "quality_flags": document["quality_flags"],
            "raw_response": {"document": document.get("raw_response", {})},
        },
    )
    evidence_item.ai_status = AIStatus.PROCESSED
    evidence_item.save(update_fields=["ai_status"])
    log_action(actor, "AZURE_DOCUMENT_INTELLIGENCE_PROCESSING_COMPLETED", evidence_item, {"borrower_profile": evidence_item.borrower_profile_id, "confidence_score": result.confidence_score})
    return result


def process_evidence_item(evidence_item, actor=None):
    if use_mock_ai():
        return _process_mock(evidence_item, actor=actor)
    if evidence_item.evidence_type == EvidenceType.BUSINESS_PHOTO:
        return _process_azure_vision(evidence_item, actor=actor)
    return _process_azure_document(evidence_item, actor=actor)


def summarize_profile_notes(profile):
    notes = [item.field_agent_note for item in profile.evidence_items.all()]
    return MockLanguageClient().summarize_notes(profile, notes)


def policy_context():
    return MockSearchClient().retrieve_policy_context()
