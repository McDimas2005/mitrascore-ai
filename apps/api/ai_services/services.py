from evidence.models import AIExtractionResult, AIStatus

from .mock_clients import MockDocumentIntelligenceClient, MockLanguageClient, MockSearchClient, MockVisionClient


def process_evidence_item(evidence_item):
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
    return result


def summarize_profile_notes(profile):
    notes = [item.field_agent_note for item in profile.evidence_items.all()]
    return MockLanguageClient().summarize_notes(profile, notes)


def policy_context():
    return MockSearchClient().retrieve_policy_context()
