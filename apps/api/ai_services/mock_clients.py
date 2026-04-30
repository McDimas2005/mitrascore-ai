from dataclasses import dataclass
from pathlib import Path


def _tokens(name):
    return Path(name or "").stem.lower().replace("-", "_").split("_")


@dataclass
class MockVisionClient:
    service_name: str = "MockVisionClient"

    def analyze_image(self, filename, evidence_type):
        joined = " ".join(_tokens(filename))
        indicators = []
        flags = []
        if evidence_type == "BUSINESS_PHOTO" or "warung" in joined or "toko" in joined:
            indicators += ["etalase terlihat", "stok barang harian", "aktivitas usaha ritel"]
        if "qris" in joined:
            indicators += ["kanal pembayaran digital", "riwayat transaksi non tunai"]
        if "blur" in joined:
            flags.append("Gambar berpotensi buram")
        confidence = 0.82 if indicators else 0.62
        return {"indicators": indicators, "quality_flags": flags, "confidence": confidence}


@dataclass
class MockDocumentIntelligenceClient:
    service_name: str = "MockDocumentIntelligenceClient"

    def extract_document(self, filename, evidence_type):
        joined = " ".join(_tokens(filename))
        if evidence_type in {"RECEIPT", "SUPPLIER_NOTE", "INVOICE"}:
            text = "Nota pemasok Warung Sari: pembelian beras, minyak, gula, dan mie instan. Total Rp 850.000."
            fields = {"vendor": "Pemasok Sembako Subang", "amount": 850000, "items": ["beras", "minyak", "gula", "mie instan"]}
            indicators = ["pembelian stok berulang", "hubungan pemasok aktif"]
            confidence = 0.86
        elif evidence_type == "QRIS_SCREENSHOT" or "qris" in joined:
            text = "Ringkasan QRIS: transaksi masuk harian stabil dengan nominal kecil berulang."
            fields = {"payment_channel": "QRIS", "daily_transaction_pattern": "stabil", "estimated_monthly_qris": 4200000}
            indicators = ["transaksi digital", "pola pendapatan harian"]
            confidence = 0.8
        elif evidence_type == "SALES_NOTE":
            text = "Catatan penjualan harian: estimasi omzet Rp 350.000 - Rp 500.000 per hari."
            fields = {"daily_sales_low": 350000, "daily_sales_high": 500000}
            indicators = ["catatan omzet harian"]
            confidence = 0.78
        else:
            text = "Bukti usaha informal terdeteksi, detail perlu diverifikasi manual."
            fields = {}
            indicators = ["bukti pendukung informal"]
            confidence = 0.64
        return {
            "extracted_text": text,
            "extracted_fields": fields,
            "indicators": indicators,
            "quality_flags": [],
            "confidence": confidence,
        }


@dataclass
class MockLanguageClient:
    service_name: str = "MockLanguageClient"

    def summarize_notes(self, profile, evidence_notes):
        category = profile.business_category or "usaha informal"
        return (
            f"Usaha {category} memiliki catatan arus kas sederhana, tujuan pembiayaan untuk {profile.financing_purpose}. "
            f"Catatan lapangan: {'; '.join([n for n in evidence_notes if n]) or 'belum ada catatan tambahan'}."
        )

    def risk_language(self, profile):
        flags = []
        if "tanpa agunan" in profile.business_note.lower() or "no collateral" in profile.business_note.lower():
            flags.append("Tidak memiliki agunan formal, perlu penekanan pada verifikasi arus kas.")
        if "bank" in profile.business_note.lower() and "tidak" in profile.business_note.lower():
            flags.append("Belum ada riwayat kredit bank formal.")
        return flags


@dataclass
class MockSearchClient:
    service_name: str = "MockSearchClient"

    def retrieve_policy_context(self):
        return {
            "data_used": ["profil usaha", "bukti usaha yang diunggah", "catatan agen", "hasil OCR/ekstraksi bukti"],
            "data_not_used": ["atribut sensitif", "pengenalan wajah", "media sosial", "kontak pribadi di luar unggahan"],
            "warning": "AI tidak menyetujui atau menolak pembiayaan. Keputusan akhir wajib dilakukan manusia.",
        }
