from decimal import Decimal

from ai_services.services import policy_context, summarize_profile_notes
from borrowers.models import BorrowerStatus
from evidence.models import AIStatus, EvidenceType, SourceType
from scoring.models import ConfidenceLevel, CreditReadinessReview, InstantEvidenceCheck, ReadinessBand


PROFILE_FIELDS = [
    "business_name",
    "business_category",
    "business_duration_months",
    "financing_purpose",
    "requested_amount",
    "estimated_monthly_revenue",
    "estimated_monthly_expense",
    "simple_cashflow_note",
]


def has_consent(profile):
    return hasattr(profile, "consent") and profile.consent.consent_given


def require_consent(profile):
    if not has_consent(profile):
        raise PermissionError("Consent is required before evidence upload or scoring.")


def calculate_completeness(profile):
    completed = 0
    missing = []
    for field in PROFILE_FIELDS:
        value = getattr(profile, field)
        if value not in ("", None, 0, Decimal("0")):
            completed += 1
        else:
            missing.append(field)
    evidence_count = profile.evidence_items.count()
    evidence_points = min(evidence_count, 4)
    score = round(((completed / len(PROFILE_FIELDS)) * 70) + ((evidence_points / 4) * 30))
    if evidence_count == 0:
        missing.append("evidence_items")
    return score, missing


def calculate_evidence_quality(profile):
    items = list(profile.evidence_items.all())
    if not items:
        return 0, ["Belum ada bukti usaha yang diunggah."]
    processed = [item for item in items if item.ai_status == AIStatus.PROCESSED and hasattr(item, "extraction_result")]
    type_diversity = len({item.evidence_type for item in items})
    verified = len([item for item in items if item.source_type == SourceType.AGENT_VERIFIED])
    avg_confidence = sum([getattr(item.extraction_result, "confidence_score", 0) for item in processed]) / max(len(processed), 1)
    score = min(100, round((type_diversity * 7) + (len(processed) * 4) + (verified * 4) + (avg_confidence * 20)))
    weak = []
    if type_diversity < 3:
        weak.append("Jenis bukti masih kurang beragam.")
    if len(processed) < len(items):
        weak.append("Sebagian bukti belum diproses OCR mock.")
    return score, weak


def collect_indicators(profile):
    indicators = []
    for item in profile.evidence_items.select_related("extraction_result"):
        if hasattr(item, "extraction_result"):
            indicators.extend(item.extraction_result.detected_business_indicators.get("indicators", []))
    return list(dict.fromkeys(indicators))


def run_instant_check(profile):
    require_consent(profile)
    completeness, missing = calculate_completeness(profile)
    quality, weak = calculate_evidence_quality(profile)
    indicators = collect_indicators(profile)
    can_submit = completeness >= 75 and quality >= 55 and len(indicators) >= 2
    steps = []
    if missing:
        steps.append("Lengkapi profil usaha dan estimasi arus kas.")
    if weak:
        steps.append("Tambahkan bukti transaksi yang lebih jelas atau terverifikasi agen.")
    if can_submit:
        steps.append("Kasus siap dikirim ke analis untuk DeepScore Review.")
    check = InstantEvidenceCheck.objects.create(
        borrower_profile=profile,
        data_completeness_score=completeness,
        evidence_quality_score=quality,
        detected_business_indicators={"indicators": indicators},
        ocr_summary="; ".join(
            [
                item.extraction_result.extracted_text
                for item in profile.evidence_items.all()
                if hasattr(item, "extraction_result")
            ][:4]
        ),
        business_note_summary=summarize_profile_notes(profile),
        missing_data=missing,
        weak_evidence=weak,
        recommended_next_steps=steps,
        can_submit_to_analyst=can_submit,
    )
    if not can_submit:
        profile.status = BorrowerStatus.NEEDS_COMPLETION
        profile.save(update_fields=["status", "updated_at"])
    elif profile.status in {BorrowerStatus.DRAFT, BorrowerStatus.CONSENTED}:
        profile.status = BorrowerStatus.EVIDENCE_UPLOADED
        profile.save(update_fields=["status", "updated_at"])
    return check


def _band(score):
    if score >= 85:
        return ReadinessBand.STRONG
    if score >= 70:
        return ReadinessBand.PROMISING
    if score >= 50:
        return ReadinessBand.MODERATE
    return ReadinessBand.LOW


def _confidence(profile, evidence_quality):
    count = profile.evidence_items.count()
    if count >= 6 and evidence_quality >= 80:
        return ConfidenceLevel.HIGH
    if count >= 3 and evidence_quality >= 55:
        return ConfidenceLevel.MEDIUM
    return ConfidenceLevel.LOW


def run_deepscore(profile, analyst):
    require_consent(profile)
    latest_check = profile.instant_checks.first() or run_instant_check(profile)
    revenue = float(profile.estimated_monthly_revenue or 0)
    expense = float(profile.estimated_monthly_expense or 0)
    margin_ratio = (revenue - expense) / revenue if revenue else 0
    requested = float(profile.requested_amount or 0)
    requested_to_revenue = requested / max(revenue, 1)

    repayment = max(20, min(100, round(45 + (margin_ratio * 90) - max(requested_to_revenue - 3, 0) * 5)))
    evidence_types = {item.evidence_type for item in profile.evidence_items.all()}
    has_receipts = EvidenceType.RECEIPT in evidence_types or EvidenceType.SUPPLIER_NOTE in evidence_types
    business_consistency = min(100, round(42 + (min(profile.business_duration_months, 36) * 0.9) + (12 if has_receipts else 0)))
    evidence_quality = latest_check.evidence_quality_score
    operational_stability = min(100, round(40 + (min(profile.business_duration_months, 30) * 0.75) + (8 if "stok" in " ".join(collect_indicators(profile)) else 0)))
    red_flags = []
    note_lower = (profile.business_note + " " + profile.simple_cashflow_note).lower()
    if "no collateral" in note_lower or "tanpa agunan" in note_lower:
        red_flags.append("Tidak ada agunan formal; gunakan verifikasi arus kas, bukan sebagai penolak otomatis.")
    if "no formal bank" in note_lower or "belum ada riwayat kredit" in note_lower:
        red_flags.append("Belum ada riwayat kredit bank formal.")
    risk_compliance = max(45, 85 - (len(red_flags) * 10))

    breakdown = {
        "repayment_capacity": {"weight": 30, "score": repayment, "weighted": round(repayment * 0.30, 1)},
        "business_consistency": {"weight": 25, "score": business_consistency, "weighted": round(business_consistency * 0.25, 1)},
        "evidence_quality": {"weight": 20, "score": evidence_quality, "weighted": round(evidence_quality * 0.20, 1)},
        "operational_stability": {"weight": 15, "score": operational_stability, "weighted": round(operational_stability * 0.15, 1)},
        "risk_compliance": {"weight": 10, "score": risk_compliance, "weighted": round(risk_compliance * 0.10, 1)},
    }
    score = round(sum(part["weighted"] for part in breakdown.values()))
    context = policy_context()
    positives = []
    indicators = collect_indicators(profile)
    if indicators:
        positives.append("Indikator usaha terdeteksi: " + ", ".join(indicators[:5]) + ".")
    if margin_ratio > 0.2:
        positives.append("Estimasi arus kas menunjukkan margin positif.")
    if has_receipts:
        positives.append("Ada bukti pembelian stok dari pemasok.")
    suggested = "Minta dua bukti transaksi tambahan dan verifikasi tujuan pembiayaan sebelum final review."
    review = CreditReadinessReview.objects.create(
        borrower_profile=profile,
        score=score,
        readiness_band=_band(score),
        confidence_level=_confidence(profile, evidence_quality),
        positive_signals=positives,
        red_flags=red_flags,
        main_reasons=[
            "Skor berbasis aturan deterministik, bukan model black-box.",
            context["warning"],
            "Bobot: kapasitas bayar 30%, konsistensi usaha 25%, kualitas bukti 20%, stabilitas 15%, risiko/kepatuhan 10%.",
        ],
        suggested_next_action=suggested,
        score_breakdown=breakdown,
        reviewed_by=analyst,
    )
    profile.status = BorrowerStatus.UNDER_REVIEW
    profile.save(update_fields=["status", "updated_at"])
    return review
