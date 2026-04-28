from decimal import Decimal

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from rest_framework.test import APIClient

from accounts.models import User, UserRole
from ai_services.services import process_evidence_item
from audit.models import AuditLog
from borrowers.models import BorrowerProfile, ConsentRecord
from evidence.models import EvidenceItem, EvidenceType, SourceType
from scoring.services import run_deepscore, run_instant_check


class MitraScoreFlowTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user("owner@test.local", "Demo123!", full_name="Owner", role=UserRole.UMKM_OWNER)
        self.agent = User.objects.create_user("agent@test.local", "Demo123!", full_name="Agent", role=UserRole.FIELD_AGENT)
        self.analyst = User.objects.create_user("analyst@test.local", "Demo123!", full_name="Analyst", role=UserRole.ANALYST)
        self.profile = BorrowerProfile.objects.create(
            owner=self.owner,
            business_name="Warung Test",
            business_category="Warung sembako",
            business_duration_months=24,
            financing_purpose="Tambah stok",
            requested_amount=Decimal("5000000"),
            estimated_monthly_revenue=Decimal("12000000"),
            estimated_monthly_expense=Decimal("8500000"),
            simple_cashflow_note="Omzet harian stabil.",
            business_note="No collateral and no formal bank credit history.",
            created_by=self.owner,
            assisted_by=self.agent,
        )
        self.client = APIClient()

    def give_consent(self):
        return ConsentRecord.objects.create(
            borrower_profile=self.profile,
            consent_given=True,
            consent_text_snapshot="Consent",
            data_processing_purpose="Purpose",
            ai_usage_disclosure="Disclosure",
            user_rights_disclosure="Rights",
            given_by=self.owner,
        )

    def add_processed_evidence(self):
        fixtures = [
            ("business_photo_warung.jpg", EvidenceType.BUSINESS_PHOTO, SourceType.SELF_UPLOADED),
            ("supplier_receipt_1.pdf", EvidenceType.RECEIPT, SourceType.AGENT_VERIFIED),
            ("supplier_receipt_2.pdf", EvidenceType.RECEIPT, SourceType.AGENT_VERIFIED),
            ("daily_sales_note.txt", EvidenceType.SALES_NOTE, SourceType.SELF_UPLOADED),
            ("qris_screenshot.png", EvidenceType.QRIS_SCREENSHOT, SourceType.SELF_UPLOADED),
        ]
        for name, evidence_type, source_type in fixtures:
            item = EvidenceItem.objects.create(
                borrower_profile=self.profile,
                evidence_type=evidence_type,
                source_type=source_type,
                file=SimpleUploadedFile(name, b"demo"),
                original_filename=name,
                mime_type="application/octet-stream",
                file_size=4,
                uploaded_by=self.owner,
            )
            process_evidence_item(item)

    def test_consent_required_before_evidence_upload_and_scoring(self):
        self.client.force_authenticate(self.owner)
        upload = SimpleUploadedFile("receipt.pdf", b"demo", content_type="application/pdf")
        response = self.client.post(
            f"/api/borrower-profiles/{self.profile.id}/evidence/",
            {"evidence_type": EvidenceType.RECEIPT, "source_type": SourceType.SELF_UPLOADED, "file": upload},
            format="multipart",
        )
        self.assertEqual(response.status_code, 403)
        with self.assertRaises(PermissionError):
            run_instant_check(self.profile)

    def test_role_permissions_block_owner_from_analyst_cases(self):
        self.client.force_authenticate(self.owner)
        response = self.client.get("/api/analyst/cases/")
        self.assertEqual(response.status_code, 403)

    def test_completeness_scoring_allows_submission_when_sufficient(self):
        self.give_consent()
        self.add_processed_evidence()
        check = run_instant_check(self.profile)
        self.assertGreaterEqual(check.data_completeness_score, 90)
        self.assertTrue(check.can_submit_to_analyst)

    def test_credit_readiness_score_breakdown_is_explainable(self):
        self.give_consent()
        self.add_processed_evidence()
        run_instant_check(self.profile)
        review = run_deepscore(self.profile, self.analyst)
        self.assertIn("repayment_capacity", review.score_breakdown)
        self.assertIn("risk_compliance", review.score_breakdown)
        self.assertGreaterEqual(review.score, 70)
        self.assertLessEqual(review.score, 80)

    def test_audit_log_creation_on_consent_endpoint(self):
        self.client.force_authenticate(self.owner)
        response = self.client.post(f"/api/borrower-profiles/{self.profile.id}/consent/", {"consent_given": True}, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertTrue(AuditLog.objects.filter(action="CONSENT_RECORDED", entity_id=str(self.profile.id)).exists())

    def test_mock_ai_extraction_is_deterministic(self):
        self.give_consent()
        item = EvidenceItem.objects.create(
            borrower_profile=self.profile,
            evidence_type=EvidenceType.RECEIPT,
            source_type=SourceType.SELF_UPLOADED,
            file=SimpleUploadedFile("supplier_receipt_beras.pdf", b"demo"),
            original_filename="supplier_receipt_beras.pdf",
            mime_type="application/pdf",
            file_size=4,
            uploaded_by=self.owner,
        )
        result = process_evidence_item(item)
        self.assertEqual(result.extracted_fields["vendor"], "Pemasok Sembako Subang")
        self.assertIn("pembelian stok berulang", result.detected_business_indicators["indicators"])
