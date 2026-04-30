from scoring.models import HumanDecision

from .models import BorrowerStatus


RECOVERABLE_REVIEW_DECISIONS = {
    HumanDecision.NEEDS_MORE_DATA,
    HumanDecision.NOT_RECOMMENDED_AT_THIS_STAGE,
}

FINAL_LOCKED_DECISIONS = {
    HumanDecision.APPROVED_FOR_FINANCING,
    HumanDecision.DECLINED,
}


STATUS_LABELS = {
    BorrowerStatus.DRAFT: "Draft profil usaha",
    BorrowerStatus.CONSENTED: "Persetujuan data tersimpan",
    BorrowerStatus.EVIDENCE_UPLOADED: "Bukti usaha diunggah",
    BorrowerStatus.NEEDS_COMPLETION: "Perlu dilengkapi",
    BorrowerStatus.READY_FOR_ANALYST: "Menunggu review analis",
    BorrowerStatus.UNDER_REVIEW: "Sedang direview analis",
    BorrowerStatus.REVIEWED: "Review selesai",
}


def latest_review(profile):
    return profile.reviews.first()


def latest_decision(profile):
    review = latest_review(profile)
    return review.final_human_decision if review else None


def is_final_locked(profile):
    return latest_decision(profile) in FINAL_LOCKED_DECISIONS


def workflow_stage(profile):
    review = latest_review(profile)
    if not hasattr(profile, "consent") or not profile.consent.consent_given:
        return {
            "code": "CONSENT_REQUIRED",
            "label": "Persetujuan data diperlukan",
            "summary": "UMKM owner harus menyetujui pemrosesan data sebelum bukti, scoring, atau review dapat berjalan.",
        }
    if review and profile.status == BorrowerStatus.READY_FOR_ANALYST:
        return {
            "code": "ANALYST_QUEUE",
            "label": "Respons terkirim ke antrean analis",
            "summary": "Owner atau field agent sudah mengirim pembaruan. Analis perlu menjalankan review ulang.",
        }
    if not review:
        latest_check = profile.instant_checks.first()
        if profile.status == BorrowerStatus.READY_FOR_ANALYST:
            return {
                "code": "ANALYST_QUEUE",
                "label": "Dalam antrean analis",
                "summary": "Kasus sudah dikirim dan menunggu analis menjalankan DeepScore Review.",
            }
        if latest_check and latest_check.can_submit_to_analyst:
            return {
                "code": "READY_TO_SUBMIT",
                "label": "Siap dikirim ke analis",
                "summary": "Instant Evidence Check sudah cukup. Owner atau field agent perlu mengirim kasus ke antrean analis.",
            }
        if profile.status == BorrowerStatus.NEEDS_COMPLETION:
            return {
                "code": "DATA_COMPLETION",
                "label": "Lengkapi data dan bukti",
                "summary": "Profil atau bukti belum cukup kuat untuk antrean analis.",
            }
        return {
            "code": "ONBOARDING",
            "label": "Onboarding dan pengumpulan bukti",
            "summary": "Lengkapi profil usaha, unggah bukti, lalu jalankan Instant Evidence Check.",
        }

    decision = review.final_human_decision
    if decision == HumanDecision.PENDING:
        return {
            "code": "HUMAN_REVIEW",
            "label": "Menunggu keputusan manusia",
            "summary": "DeepScore sudah tersedia dan analis sedang menentukan keputusan manusia.",
        }
    if decision == HumanDecision.NEEDS_MORE_DATA:
        return {
            "code": "ANALYST_REQUESTED_DATA",
            "label": "Analis meminta data tambahan",
            "summary": "UMKM owner atau field agent perlu merespons catatan analis dengan bukti atau klarifikasi tambahan.",
        }
    if decision == HumanDecision.RECOMMENDED_FOR_REVIEW:
        return {
            "code": "FINAL_REVIEW",
            "label": "Direkomendasikan untuk review pembiayaan lanjutan",
            "summary": "Kasus layak masuk review pembiayaan lanjutan, tetapi belum menjadi persetujuan pinjaman final.",
        }
    if decision == HumanDecision.APPROVED_FOR_FINANCING:
        return {
            "code": "APPROVED",
            "label": "Disetujui manusia untuk proses pembiayaan",
            "summary": "Analis memberi keputusan manusia positif. Lanjutkan proses operasional pembiayaan sesuai kebijakan lembaga.",
        }
    if decision == HumanDecision.DECLINED:
        return {
            "code": "DECLINED",
            "label": "Ditolak pada review manusia",
            "summary": "Pengajuan ini sudah ditutup untuk siklus review saat ini. Perubahan normal, unggah bukti, dan kirim ulang tidak tersedia kecuali analis atau admin membuka ulang kasus.",
        }
    return {
        "code": "NOT_READY",
        "label": "Belum direkomendasikan pada tahap ini",
        "summary": "Kasus belum cukup kuat untuk lanjut. Perbaiki red flags, bukti, dan klarifikasi usaha sebelum mengajukan kembali.",
    }


def role_next_actions(profile):
    stage = workflow_stage(profile)["code"]
    common_wait = ["Pantau audit trail dan pembaruan status kasus."]
    actions = {
        "UMKM_OWNER": [],
        "FIELD_AGENT": [],
        "ANALYST": [],
        "ADMIN": [],
    }

    if stage == "CONSENT_REQUIRED":
        actions["UMKM_OWNER"] = ["Buka onboarding dan berikan persetujuan data.", "Lengkapi profil usaha awal."]
        actions["FIELD_AGENT"] = ["Bantu owner memahami persetujuan data dan kebutuhan onboarding."]
        actions["ANALYST"] = ["Belum ada aksi analis sampai consent dan bukti tersedia."]
    elif stage == "ONBOARDING":
        actions["UMKM_OWNER"] = ["Lengkapi profil usaha.", "Unggah bukti usaha.", "Jalankan Instant Evidence Check."]
        actions["FIELD_AGENT"] = ["Bantu unggah atau verifikasi bukti jika diminta owner.", "Tambahkan catatan observasi lapangan."]
        actions["ANALYST"] = ["Tunggu kasus dikirim ke antrean analis."]
    elif stage == "DATA_COMPLETION":
        actions["UMKM_OWNER"] = ["Lengkapi data yang kurang.", "Unggah bukti tambahan.", "Jalankan ulang Instant Evidence Check dan kirim kembali ke analis."]
        actions["FIELD_AGENT"] = ["Verifikasi bukti tambahan.", "Tambahkan observasi lapangan yang menjawab kekurangan data."]
        actions["ANALYST"] = ["Tunggu respons owner atau field agent, lalu review ulang setelah resubmission."]
    elif stage == "READY_TO_SUBMIT":
        actions["UMKM_OWNER"] = ["Kirim kasus ke analis.", "Pastikan data kontak dan tujuan pembiayaan sudah benar."]
        actions["FIELD_AGENT"] = ["Kirim respons atau kasus dampingan ke analis.", "Pastikan bukti yang diverifikasi sudah ditandai dengan benar."]
        actions["ANALYST"] = ["Tunggu kasus masuk ke antrean analis."]
    elif stage == "ANALYST_QUEUE":
        actions["UMKM_OWNER"] = ["Tunggu analis menjalankan DeepScore Review.", *common_wait]
        actions["FIELD_AGENT"] = ["Pastikan bukti terverifikasi bila kasus ini didampingi.", *common_wait]
        actions["ANALYST"] = ["Buka kasus.", "Jalankan DeepScore Review.", "Periksa bukti, red flags, dan audit trail."]
    elif stage == "HUMAN_REVIEW":
        actions["UMKM_OWNER"] = ["Tunggu keputusan manusia dari analis.", *common_wait]
        actions["FIELD_AGENT"] = ["Siap membantu klarifikasi jika analis meminta data tambahan."]
        actions["ANALYST"] = ["Isi catatan analis.", "Pilih: perlu data, rekomendasikan review lanjutan, belum direkomendasikan, setujui, atau tolak."]
    elif stage == "ANALYST_REQUESTED_DATA":
        actions["UMKM_OWNER"] = ["Baca catatan analis.", "Unggah data atau bukti tambahan.", "Jalankan ulang check dan kirim kembali ke analis."]
        actions["FIELD_AGENT"] = ["Bantu owner mengumpulkan bukti yang diminta analis.", "Tandai bukti sebagai agent verified bila sudah diverifikasi."]
        actions["ANALYST"] = ["Tunggu respons owner atau field agent.", "Review ulang setelah kasus kembali ke antrean analis."]
    elif stage == "FINAL_REVIEW":
        actions["UMKM_OWNER"] = ["Siapkan dokumen pendukung pembiayaan lanjutan.", "Pastikan kontak usaha aktif."]
        actions["FIELD_AGENT"] = ["Bantu klarifikasi final bila diminta."]
        actions["ANALYST"] = ["Selesaikan review final.", "Pilih setujui pembiayaan atau tolak dengan alasan yang jelas."]
    elif stage == "APPROVED":
        actions["UMKM_OWNER"] = ["Tunggu instruksi pencairan atau proses pembiayaan berikutnya.", "Simpan bukti dan catatan review untuk referensi."]
        actions["FIELD_AGENT"] = ["Tidak ada aksi lapangan kecuali diminta untuk verifikasi akhir."]
        actions["ANALYST"] = ["Pastikan keputusan, catatan, dan audit trail sudah lengkap."]
    elif stage == "DECLINED":
        actions["UMKM_OWNER"] = [
            "Baca alasan penolakan dan simpan catatan review.",
            "Pengajuan ini tidak dapat diedit atau dikirim ulang dari siklus yang sama.",
            "Jika ingin mencoba lagi, mulai pengajuan baru atau minta klarifikasi resmi sesuai kebijakan lembaga.",
        ]
        actions["FIELD_AGENT"] = [
            "Jelaskan alasan penolakan tanpa mengubah bukti pada kasus yang sudah ditutup.",
            "Bantu owner menyiapkan pengajuan baru hanya bila kebijakan lembaga mengizinkan.",
        ]
        actions["ANALYST"] = [
            "Tidak ada aksi lanjutan pada kasus tertutup.",
            "Gunakan undo ke pending hanya jika keputusan perlu dikoreksi atau kasus resmi dibuka ulang.",
        ]
    else:
        actions["UMKM_OWNER"] = ["Baca catatan analis.", "Perbaiki red flags dan bukti usaha.", "Ajukan kembali setelah data lebih kuat."]
        actions["FIELD_AGENT"] = ["Bantu owner memperkuat bukti dan observasi lapangan."]
        actions["ANALYST"] = ["Tunggu pengajuan ulang setelah perbaikan."]

    actions["ADMIN"] = actions["ANALYST"]
    return actions
