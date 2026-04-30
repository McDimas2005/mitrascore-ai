from rest_framework import serializers

from ai_services.services import policy_context

from .models import CreditReadinessReview, HumanDecision, InstantEvidenceCheck


HUMAN_DECISION_LABELS = {
    HumanDecision.PENDING: "Menunggu keputusan reviewer",
    HumanDecision.NEEDS_MORE_DATA: "Perlu data tambahan",
    HumanDecision.RECOMMENDED_FOR_REVIEW: "Direkomendasikan untuk review lanjutan",
    HumanDecision.NOT_RECOMMENDED_AT_THIS_STAGE: "Belum direkomendasikan pada tahap ini",
    HumanDecision.APPROVED_FOR_FINANCING: "Disetujui untuk proses pembiayaan",
    HumanDecision.DECLINED: "Ditolak final pada review manusia",
}

HUMAN_DECISION_FOLLOW_UP_ACTIONS = {
    HumanDecision.PENDING: [
        "Tunggu reviewer menyelesaikan keputusan manusia.",
        "Pastikan kontak usaha aktif jika reviewer membutuhkan klarifikasi.",
        "Pantau dashboard ini untuk hasil review terbaru.",
    ],
    HumanDecision.NEEDS_MORE_DATA: [
        "Baca catatan reviewer dan lengkapi data atau bukti yang diminta.",
        "Unggah bukti tambahan seperti nota penjualan, nota pemasok, foto usaha, atau QRIS.",
        "Jalankan ulang Instant Evidence Check setelah bukti ditambahkan.",
        "Kirim kembali kasus ke analis atau minta bantuan field agent bila perlu verifikasi lapangan.",
    ],
    HumanDecision.RECOMMENDED_FOR_REVIEW: [
        "Siapkan dokumen pendukung untuk review pembiayaan lanjutan.",
        "Pastikan nomor kontak dan informasi usaha tetap dapat dihubungi.",
        "Tindak lanjuti permintaan klarifikasi dari reviewer atau mitra pembiayaan.",
        "Jangan menganggap hasil ini sebagai persetujuan pembiayaan otomatis.",
    ],
    HumanDecision.NOT_RECOMMENDED_AT_THIS_STAGE: [
        "Tinjau red flags dan catatan reviewer untuk memahami area yang perlu diperbaiki.",
        "Perkuat bukti arus kas, konsistensi transaksi, dan verifikasi usaha.",
        "Minta bantuan field agent jika perlu pendampingan melengkapi bukti.",
        "Ajukan kembali setelah data dan bukti usaha lebih kuat.",
    ],
    HumanDecision.APPROVED_FOR_FINANCING: [
        "Tunggu instruksi proses pembiayaan berikutnya dari analis atau mitra pembiayaan.",
        "Pastikan data kontak, identitas usaha, dan dokumen pendukung tetap siap diverifikasi.",
        "Simpan catatan review dan bukti usaha untuk proses administrasi lanjutan.",
    ],
    HumanDecision.DECLINED: [
        "Baca catatan reviewer untuk memahami alasan penolakan final pada siklus ini.",
        "Pengajuan ini tidak dapat diedit, ditambah bukti, atau dikirim ulang dari siklus yang sama.",
        "Ajukan pengajuan baru hanya jika kebijakan lembaga mengizinkan dan data usaha sudah berubah secara material.",
        "Gunakan kanal klarifikasi resmi bila menurut owner ada kekeliruan keputusan.",
    ],
}


class InstantEvidenceCheckSerializer(serializers.ModelSerializer):
    class Meta:
        model = InstantEvidenceCheck
        fields = (
            "id",
            "borrower_profile",
            "data_completeness_score",
            "evidence_quality_score",
            "detected_business_indicators",
            "ocr_summary",
            "business_note_summary",
            "missing_data",
            "weak_evidence",
            "recommended_next_steps",
            "can_submit_to_analyst",
            "created_at",
        )


class CreditReadinessReviewSerializer(serializers.ModelSerializer):
    reviewed_by_email = serializers.EmailField(source="reviewed_by.email", read_only=True)
    final_human_decision_label = serializers.SerializerMethodField()
    follow_up_actions = serializers.SerializerMethodField()
    data_used = serializers.SerializerMethodField()
    data_not_used = serializers.SerializerMethodField()
    confidence_explanation = serializers.SerializerMethodField()
    model_limitations = serializers.SerializerMethodField()

    class Meta:
        model = CreditReadinessReview
        fields = (
            "id",
            "borrower_profile",
            "score",
            "readiness_band",
            "confidence_level",
            "positive_signals",
            "red_flags",
            "main_reasons",
            "suggested_next_action",
            "score_breakdown",
            "data_used",
            "data_not_used",
            "confidence_explanation",
            "model_limitations",
            "analyst_notes",
            "final_human_decision",
            "final_human_decision_label",
            "follow_up_actions",
            "reviewed_by",
            "reviewed_by_email",
            "reviewed_at",
            "created_at",
        )
        read_only_fields = ("score", "readiness_band", "confidence_level", "reviewed_by", "reviewed_at")

    def get_final_human_decision_label(self, obj):
        return HUMAN_DECISION_LABELS.get(obj.final_human_decision, obj.get_final_human_decision_display())

    def get_follow_up_actions(self, obj):
        return HUMAN_DECISION_FOLLOW_UP_ACTIONS.get(obj.final_human_decision, [])

    def get_data_used(self, obj):
        return policy_context()["data_used"]

    def get_data_not_used(self, obj):
        return policy_context()["data_not_used"]

    def get_confidence_explanation(self, obj):
        return {
            "HIGH": "Evidence complete and consistent.",
            "MEDIUM": "Enough evidence but some uncertainty remains.",
            "LOW": "Limited or weak evidence.",
        }.get(obj.confidence_level, "Evidence confidence needs human interpretation.")

    def get_model_limitations(self, obj):
        return [
            "DeepScore is deterministic decision-support, not an automated financing decision.",
            "Azure OCR or Vision outputs can miss unclear, cropped, handwritten, or low-light evidence.",
            "No face recognition, protected attribute scoring, social media scraping, or sensitive attribute inference is used.",
            "Human analyst review is required for every final financing decision.",
        ]
