from decimal import Decimal

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.test import override_settings

from accounts.models import User, UserRole
from ai_services.services import process_evidence_item
from audit.services import log_action
from borrowers.models import BorrowerProfile, BorrowerStatus, ConsentRecord
from evidence.models import EvidenceItem, EvidenceType, SourceType
from scoring.services import run_deepscore, run_instant_check


DEMO_PASSWORD = "Demo123!"


class Command(BaseCommand):
    help = "Seed MitraScore AI demo users and Ibu Sari case."

    def handle(self, *args, **options):
        users = {
            "umkm@mitrascore.demo": ("Ibu Sari", UserRole.UMKM_OWNER),
            "umkm2@mitrascore.demo": ("Pak Andi Test UMKM", UserRole.UMKM_OWNER),
            "fieldagent@mitrascore.demo": ("Budi Field Agent", UserRole.FIELD_AGENT),
            "analyst@mitrascore.demo": ("Rina Credit Analyst", UserRole.ANALYST),
            "admin@mitrascore.demo": ("Admin MitraScore", UserRole.ADMIN),
        }
        created_users = {}
        for email, (name, role) in users.items():
            user, created = User.objects.get_or_create(
                email=email,
                defaults={"full_name": name, "role": role, "is_staff": role == UserRole.ADMIN, "is_superuser": role == UserRole.ADMIN},
            )
            user.full_name = name
            user.role = role
            user.is_staff = role == UserRole.ADMIN
            user.is_superuser = role == UserRole.ADMIN
            user.set_password(DEMO_PASSWORD)
            user.save()
            created_users[email] = user
            self.stdout.write(("Created" if created else "Updated") + f" {email}")

        owner = created_users["umkm@mitrascore.demo"]
        agent = created_users["fieldagent@mitrascore.demo"]
        analyst = created_users["analyst@mitrascore.demo"]
        profile, _ = BorrowerProfile.objects.update_or_create(
            owner=owner,
            business_name="Warung Ibu Sari",
            defaults={
                "business_category": "Warung sembako",
                "business_duration_months": 30,
                "financing_purpose": "Menambah stok inventori harian",
                "requested_amount": Decimal("5000000"),
                "estimated_monthly_revenue": Decimal("12000000"),
                "estimated_monthly_expense": Decimal("8500000"),
                "simple_cashflow_note": "Omzet harian diperkirakan Rp350.000 sampai Rp500.000. Tidak ada laporan keuangan formal.",
                "business_note": "Warung di Subang. No collateral, no formal bank credit history, no formal financial statement.",
                "created_by": owner,
                "assisted_by": agent,
                "status": BorrowerStatus.CONSENTED,
            },
        )
        ConsentRecord.objects.update_or_create(
            borrower_profile=profile,
            defaults={
                "consent_given": True,
                "consent_text_snapshot": "Demo consent for local processing.",
                "data_processing_purpose": "Menilai kesiapan kredit UMKM berdasarkan bukti usaha.",
                "ai_usage_disclosure": "AI mock membantu ekstraksi dan skor berbasis aturan; tidak membuat keputusan pembiayaan.",
                "user_rights_disclosure": "Pengguna dapat meminta koreksi data dan tinjauan manusia.",
                "given_by": owner,
            },
        )
        profile.instant_checks.all().delete()
        profile.reviews.all().delete()
        fixtures = [
            ("business_photo_warung_sari.jpg", EvidenceType.BUSINESS_PHOTO, SourceType.SELF_UPLOADED, ""),
            ("supplier_receipt_beras_minyak_1.pdf", EvidenceType.RECEIPT, SourceType.AGENT_VERIFIED, "Nota asli dilihat saat kunjungan."),
            ("supplier_receipt_gula_2.pdf", EvidenceType.RECEIPT, SourceType.AGENT_VERIFIED, "Pemasok dikenal warga sekitar."),
            ("supplier_receipt_mie_3.pdf", EvidenceType.RECEIPT, SourceType.AGENT_ASSISTED, "Foto nota dibantu agen."),
            ("daily_sales_note.txt", EvidenceType.SALES_NOTE, SourceType.SELF_UPLOADED, ""),
            ("qris_screenshot_warung_sari.png", EvidenceType.QRIS_SCREENSHOT, SourceType.SELF_UPLOADED, ""),
        ]
        with override_settings(USE_MOCK_AI=True):
            for filename, evidence_type, source_type, note in fixtures:
                item, created = EvidenceItem.objects.get_or_create(
                    borrower_profile=profile,
                    original_filename=filename,
                    defaults={
                        "evidence_type": evidence_type,
                        "source_type": source_type,
                        "file": ContentFile(b"local demo evidence", name=f"evidence/{filename}"),
                        "mime_type": "application/octet-stream",
                        "file_size": 19,
                        "uploaded_by": agent if source_type != SourceType.SELF_UPLOADED else owner,
                        "field_agent_note": note,
                    },
                )
                if not created:
                    item.evidence_type = evidence_type
                    item.source_type = source_type
                    item.field_agent_note = note
                    item.save()
                process_evidence_item(item)
            run_instant_check(profile)
            review = run_deepscore(profile, analyst)
        log_action(analyst, "DEMO_DATA_SEEDED", profile, {"score": review.score})
        self.stdout.write(self.style.SUCCESS(f"Seeded demo case with score {review.score}/{100} ({review.readiness_band})."))
