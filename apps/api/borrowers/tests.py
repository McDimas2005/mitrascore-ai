from decimal import Decimal
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from accounts.models import User, UserRole
from ai_services.services import process_evidence_item
from audit.models import AuditLog
from borrowers.models import BorrowerProfile, ConsentRecord
from evidence.models import EvidenceItem, EvidenceType, SourceType
from scoring.models import HumanDecision
from scoring.services import run_deepscore, run_instant_check


TEST_MEDIA_ROOT = tempfile.mkdtemp(prefix="mitrascore-test-media-")


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
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
                field_agent_note="Bukti diverifikasi agen saat kunjungan." if source_type == SourceType.AGENT_VERIFIED else "",
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

    def test_umkm_owner_can_have_multiple_business_profiles(self):
        second_profile = BorrowerProfile.objects.create(
            owner=self.owner,
            business_name="Catering Test",
            business_category="Katering rumahan",
            business_duration_months=12,
            financing_purpose="Tambah alat masak",
            requested_amount=Decimal("3000000"),
            estimated_monthly_revenue=Decimal("8000000"),
            estimated_monthly_expense=Decimal("5500000"),
            simple_cashflow_note="Pesanan mingguan stabil.",
            business_note="Usaha terpisah dari warung.",
            created_by=self.owner,
        )
        other_owner = User.objects.create_user("owner2@test.local", "Demo123!", full_name="Owner 2", role=UserRole.UMKM_OWNER)
        other_profile = BorrowerProfile.objects.create(
            owner=other_owner,
            business_name="Laundry Owner Lain",
            business_category="Laundry",
            created_by=other_owner,
        )
        self.client.force_authenticate(self.owner)

        response = self.client.get("/api/borrower-profiles/")
        self.assertEqual(response.status_code, 200, response.content)
        profile_ids = {profile["id"] for profile in response.data}
        self.assertIn(self.profile.id, profile_ids)
        self.assertIn(second_profile.id, profile_ids)
        self.assertNotIn(other_profile.id, profile_ids)

        response = self.client.post(
            "/api/borrower-profiles/",
            {
                "business_name": "Reseller Test",
                "business_category": "Reseller makanan",
                "financing_purpose": "Tambah stok reseller",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201, response.content)
        self.assertEqual(response.data["owner"], self.owner.id)
        self.assertEqual(response.data["business_name"], "Reseller Test")

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

    def test_approval_requires_verified_decision_critical_evidence(self):
        self.give_consent()
        self.add_processed_evidence()
        run_instant_check(self.profile)
        review = run_deepscore(self.profile, self.analyst)
        self.client.force_authenticate(self.analyst)

        response = self.client.get(f"/api/borrower-profiles/{self.profile.id}/")
        self.assertEqual(response.status_code, 200, response.content)
        readiness = response.data["verification_readiness"]
        self.assertFalse(readiness["approval_ready"])
        self.assertEqual(readiness["verified_cashflow_count"], 2)
        self.assertEqual(readiness["verified_business_presence_count"], 0)

        response = self.client.patch(
            f"/api/analyst/reviews/{review.id}/decision/",
            {"final_human_decision": "APPROVED_FOR_FINANCING", "analyst_notes": "Mencoba approve tanpa verifikasi bisnis."},
            format="json",
        )
        self.assertEqual(response.status_code, 400, response.content)
        self.assertIn("verification_readiness", response.data)

        business_photo = EvidenceItem.objects.get(borrower_profile=self.profile, evidence_type=EvidenceType.BUSINESS_PHOTO)
        business_photo.source_type = SourceType.AGENT_VERIFIED
        business_photo.field_agent_note = "Foto usaha dicocokkan dengan lokasi dan stok saat kunjungan."
        business_photo.save(update_fields=["source_type", "field_agent_note"])

        response = self.client.patch(
            f"/api/analyst/reviews/{review.id}/decision/",
            {"final_human_decision": "APPROVED_FOR_FINANCING", "analyst_notes": "Bukti kunci sudah diverifikasi."},
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.data["final_human_decision"], "APPROVED_FOR_FINANCING")

    def test_owner_receives_review_decision_with_follow_up_actions(self):
        self.give_consent()
        self.add_processed_evidence()
        run_instant_check(self.profile)
        review = run_deepscore(self.profile, self.analyst)
        self.client.force_authenticate(self.owner)

        for decision in HumanDecision.values:
            review.final_human_decision = decision
            review.save(update_fields=["final_human_decision"])
            response = self.client.get("/api/borrower-profiles/")
            self.assertEqual(response.status_code, 200, response.content)
            owner_review = response.data[0]["latest_review"]
            self.assertEqual(owner_review["final_human_decision"], decision)
            self.assertTrue(owner_review["final_human_decision_label"])
            self.assertTrue(owner_review["follow_up_actions"])

    def test_owner_can_request_field_agent_help_when_review_needs_more_data(self):
        self.give_consent()
        self.add_processed_evidence()
        run_instant_check(self.profile)
        review = run_deepscore(self.profile, self.analyst)
        review.final_human_decision = HumanDecision.NEEDS_MORE_DATA
        review.save(update_fields=["final_human_decision"])
        self.profile.assisted_by = None
        self.profile.save(update_fields=["assisted_by"])
        self.client.force_authenticate(self.owner)

        response = self.client.post(
            "/api/borrower-profiles/request-field-agent-assist/",
            {"profile_id": self.profile.id, "assistance_note": "Reviewer meminta bukti transaksi tambahan."},
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.data["assisted_by_detail"]["id"], self.agent.id)

    def test_declined_review_locks_same_application_from_normal_corrections(self):
        self.give_consent()
        self.add_processed_evidence()
        run_instant_check(self.profile)
        review = run_deepscore(self.profile, self.analyst)
        self.client.force_authenticate(self.analyst)
        response = self.client.patch(
            f"/api/analyst/reviews/{review.id}/decision/",
            {"final_human_decision": "DECLINED", "analyst_notes": "Ditolak karena bukti arus kas tidak konsisten."},
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.data["final_human_decision_label"], "Ditolak final pada review manusia")

        self.client.force_authenticate(self.owner)
        response = self.client.patch(
            f"/api/borrower-profiles/{self.profile.id}/",
            {"simple_cashflow_note": "Owner mencoba memperbaiki kasus yang sudah ditolak."},
            format="json",
        )
        self.assertEqual(response.status_code, 403, response.content)

        upload = SimpleUploadedFile("after_decline_receipt.pdf", b"demo", content_type="application/pdf")
        response = self.client.post(
            f"/api/borrower-profiles/{self.profile.id}/evidence/",
            {"evidence_type": EvidenceType.RECEIPT, "source_type": SourceType.SELF_UPLOADED, "file": upload},
            format="multipart",
        )
        self.assertEqual(response.status_code, 403, response.content)

        response = self.client.post(f"/api/borrower-profiles/{self.profile.id}/instant-check/", {}, format="json")
        self.assertEqual(response.status_code, 403, response.content)

        response = self.client.post(f"/api/borrower-profiles/{self.profile.id}/submit-to-analyst/", {}, format="json")
        self.assertEqual(response.status_code, 400, response.content)

        self.profile.assisted_by = None
        self.profile.save(update_fields=["assisted_by"])
        response = self.client.post(
            "/api/borrower-profiles/request-field-agent-assist/",
            {"profile_id": self.profile.id, "assistance_note": "Minta bantuan untuk kasus yang sudah ditolak."},
            format="json",
        )
        self.assertEqual(response.status_code, 400, response.content)

    def test_not_recommended_remains_recoverable_for_owner_or_agent_response(self):
        self.give_consent()
        self.add_processed_evidence()
        run_instant_check(self.profile)
        review = run_deepscore(self.profile, self.analyst)
        self.client.force_authenticate(self.analyst)
        response = self.client.patch(
            f"/api/analyst/reviews/{review.id}/decision/",
            {
                "final_human_decision": "NOT_RECOMMENDED_AT_THIS_STAGE",
                "analyst_notes": "Perlu bukti arus kas yang lebih kuat sebelum direview lagi.",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.content)

        self.client.force_authenticate(self.owner)
        response = self.client.patch(
            f"/api/borrower-profiles/{self.profile.id}/",
            {"simple_cashflow_note": "Owner menambahkan ringkasan transaksi harian yang lebih lengkap."},
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.content)

        response = self.client.post(f"/api/borrower-profiles/{self.profile.id}/submit-to-analyst/", {}, format="json")
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.data["workflow_stage"]["code"], "ANALYST_QUEUE")

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

    def test_evidence_source_types_are_explained_and_verified_requires_note(self):
        self.give_consent()
        item = EvidenceItem.objects.create(
            borrower_profile=self.profile,
            evidence_type=EvidenceType.RECEIPT,
            source_type=SourceType.SELF_UPLOADED,
            file=SimpleUploadedFile("source_type_receipt.pdf", b"demo"),
            original_filename="source_type_receipt.pdf",
            mime_type="application/pdf",
            file_size=4,
            uploaded_by=self.owner,
        )
        self.client.force_authenticate(self.agent)

        response = self.client.patch(
            f"/api/evidence/{item.id}/source-type/",
            {"source_type": "AGENT_VERIFIED", "field_agent_note": ""},
            format="json",
        )
        self.assertEqual(response.status_code, 400, response.content)

        response = self.client.patch(
            f"/api/evidence/{item.id}/source-type/",
            {"source_type": "AGENT_VERIFIED", "field_agent_note": "Nota asli dilihat saat kunjungan."},
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.data["source_type_label"], "Diverifikasi agen")
        self.assertIn("kualitas bukti", response.data["source_type_effect"])

    def test_umkm_owner_can_request_field_agent_assistance(self):
        self.client.force_authenticate(self.owner)
        response = self.client.post("/api/borrower-profiles/request-field-agent-assist/", {}, format="json")
        self.assertEqual(response.status_code, 201, response.content)
        self.assertEqual(response.data["owner"], self.owner.id)
        self.assertEqual(response.data["assisted_by_detail"]["id"], self.agent.id)
        self.assertTrue(response.data["business_name"].startswith("Permintaan Bantuan Agen - "))
        self.assertTrue(
            AuditLog.objects.filter(
                action="FIELD_AGENT_ASSISTANCE_REQUESTED",
                entity_id=str(response.data["id"]),
            ).exists()
        )

        self.client.force_authenticate(self.agent)
        response = self.client.get("/api/borrower-profiles/")
        self.assertEqual(response.status_code, 200, response.content)
        self.assertTrue(any(profile["business_name"].startswith("Permintaan Bantuan Agen - ") for profile in response.data))

    def test_umkm_owner_can_request_field_agent_assistance_for_existing_draft(self):
        self.client.force_authenticate(self.owner)
        response = self.client.post(
            "/api/borrower-profiles/request-field-agent-assist/",
            {
                "profile_id": self.profile.id,
                "store_address": "Jl. Contoh No. 12, dekat pasar",
                "contact_phone": "0800-0000-DEMO",
                "preferred_visit_time": "Senin pagi",
                "assistance_note": "Butuh bantuan foto bukti dan cek nota.",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.assisted_by, self.agent)
        self.assertIn("Jl. Contoh No. 12", self.profile.business_note)
        self.assertIn("Senin pagi", self.profile.business_note)
        self.assertTrue(
            AuditLog.objects.filter(
                action="FIELD_AGENT_ASSISTANCE_REQUESTED",
                entity_id=str(self.profile.id),
                metadata__store_address="Jl. Contoh No. 12, dekat pasar",
            ).exists()
        )

    def test_owner_can_revoke_consent_delete_evidence_and_profile(self):
        self.give_consent()
        self.client.force_authenticate(self.owner)
        item = EvidenceItem.objects.create(
            borrower_profile=self.profile,
            evidence_type=EvidenceType.RECEIPT,
            source_type=SourceType.SELF_UPLOADED,
            file=SimpleUploadedFile("delete_me.pdf", b"demo"),
            original_filename="delete_me.pdf",
            mime_type="application/pdf",
            file_size=4,
            uploaded_by=self.owner,
        )
        response = self.client.delete(f"/api/evidence/{item.id}/")
        self.assertEqual(response.status_code, 204, response.content)
        self.assertFalse(EvidenceItem.objects.filter(pk=item.id).exists())

        response = self.client.post(f"/api/borrower-profiles/{self.profile.id}/consent/", {"consent_given": False}, format="json")
        self.assertEqual(response.status_code, 201, response.content)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.status, "DRAFT")

        response = self.client.delete(f"/api/borrower-profiles/{self.profile.id}/")
        self.assertEqual(response.status_code, 204, response.content)
        self.assertFalse(BorrowerProfile.objects.filter(pk=self.profile.id).exists())


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class MitraScoreEndToEndApiTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user("umkm@mitrascore.demo", "Demo123!", full_name="Ibu Demo", role=UserRole.UMKM_OWNER)
        self.agent = User.objects.create_user("fieldagent@mitrascore.demo", "Demo123!", full_name="Agen Demo", role=UserRole.FIELD_AGENT)
        self.analyst = User.objects.create_user("analyst@mitrascore.demo", "Demo123!", full_name="Analis Demo", role=UserRole.ANALYST)
        self.client = APIClient()

    def login(self, email):
        response = self.client.post("/api/auth/login/", {"email": email, "password": "Demo123!"}, format="json")
        self.assertEqual(response.status_code, 200, response.content)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")
        return response.data["user"]

    def upload_and_process(self, profile_id, filename, evidence_type, source_type="SELF_UPLOADED", note=""):
        upload = SimpleUploadedFile(filename, b"demo evidence", content_type="application/octet-stream")
        response = self.client.post(
            f"/api/borrower-profiles/{profile_id}/evidence/",
            {"evidence_type": evidence_type, "source_type": source_type, "field_agent_note": note, "file": upload},
            format="multipart",
        )
        self.assertEqual(response.status_code, 201, response.content)
        item_id = response.data["id"]
        response = self.client.post(f"/api/evidence/{item_id}/process/", {}, format="json")
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.data["ai_status"], "PROCESSED")
        return item_id

    def test_full_umkm_analyst_and_field_agent_demo_flow(self):
        # 1. Login as UMKM Owner
        owner_user = self.login("umkm@mitrascore.demo")
        self.assertEqual(owner_user["role"], "UMKM_OWNER")

        # 2. Open UMKM Self-Onboarding Mode, 3. Read and accept consent, 4. Fill business profile
        response = self.client.post(
            "/api/borrower-profiles/",
            {
                "business_name": "Warung E2E Ibu Sari",
                "business_category": "Warung sembako",
                "business_duration_months": 30,
                "financing_purpose": "Menambah stok inventori harian",
                "requested_amount": "5000000",
                "estimated_monthly_revenue": "12000000",
                "estimated_monthly_expense": "8500000",
                "simple_cashflow_note": "Omzet harian Rp350.000 sampai Rp500.000.",
                "business_note": "No collateral, no formal bank credit history, no formal financial statement.",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201, response.content)
        profile_id = response.data["id"]

        response = self.client.post(f"/api/borrower-profiles/{profile_id}/consent/", {"consent_given": True}, format="json")
        self.assertEqual(response.status_code, 201, response.content)
        self.assertTrue(response.data["consent_given"])

        # Assign this case to the demo field agent to mirror an assisted case in the local MVP.
        profile = BorrowerProfile.objects.get(pk=profile_id)
        profile.assisted_by = self.agent
        profile.save(update_fields=["assisted_by"])

        # 5. Upload business photo and transaction evidence
        self.upload_and_process(profile_id, "business_photo_warung_e2e.jpg", EvidenceType.BUSINESS_PHOTO)
        self.upload_and_process(profile_id, "supplier_receipt_beras_1.pdf", EvidenceType.RECEIPT)
        self.upload_and_process(profile_id, "supplier_receipt_minyak_2.pdf", EvidenceType.RECEIPT)
        self.upload_and_process(profile_id, "qris_screenshot_e2e.png", EvidenceType.QRIS_SCREENSHOT)

        # 6. Run Instant Evidence Check, 7. Complete missing data if needed
        response = self.client.post(f"/api/borrower-profiles/{profile_id}/instant-check/", {}, format="json")
        self.assertEqual(response.status_code, 201, response.content)
        if not response.data["can_submit_to_analyst"]:
            patch = self.client.patch(
                f"/api/borrower-profiles/{profile_id}/",
                {"simple_cashflow_note": "Omzet dan biaya sudah dilengkapi dari catatan harian."},
                format="json",
            )
            self.assertEqual(patch.status_code, 200, patch.content)
            self.upload_and_process(profile_id, "daily_sales_note_e2e.txt", EvidenceType.SALES_NOTE)
            response = self.client.post(f"/api/borrower-profiles/{profile_id}/instant-check/", {}, format="json")
            self.assertEqual(response.status_code, 201, response.content)
        self.assertTrue(response.data["can_submit_to_analyst"], response.data)

        # 8. Submit case to Analyst Dashboard
        response = self.client.post(f"/api/borrower-profiles/{profile_id}/submit-to-analyst/", {}, format="json")
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.data["status"], "READY_FOR_ANALYST")

        response = self.client.post(f"/api/borrower-profiles/{profile_id}/undo-submit-to-analyst/", {}, format="json")
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.data["status"], "NEEDS_COMPLETION")

        response = self.client.post(f"/api/borrower-profiles/{profile_id}/submit-to-analyst/", {}, format="json")
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.data["status"], "READY_FOR_ANALYST")

        # 9. Login as Analyst, 10. Open submitted case
        analyst_user = self.login("analyst@mitrascore.demo")
        self.assertEqual(analyst_user["role"], "ANALYST")
        response = self.client.get("/api/analyst/cases/")
        self.assertEqual(response.status_code, 200, response.content)
        self.assertTrue(any(case["id"] == profile_id for case in response.data))

        response = self.client.get(f"/api/analyst/cases/{profile_id}/")
        self.assertEqual(response.status_code, 200, response.content)
        self.assertGreaterEqual(len(response.data["evidence_items"]), 4)
        self.assertIsNotNone(response.data["consent"])

        # 11. Run DeepScore Review
        response = self.client.post(f"/api/analyst/cases/{profile_id}/deepscore/", {}, format="json")
        self.assertEqual(response.status_code, 201, response.content)
        review_id = response.data["id"]

        # 12. Check score, red flags, positive signals, confidence, audit trail, Responsible AI data
        self.assertGreaterEqual(response.data["score"], 70)
        self.assertLessEqual(response.data["score"], 85)
        self.assertEqual(response.data["readiness_band"], "PROMISING")
        self.assertEqual(response.data["confidence_level"], "LOW")
        self.assertTrue(response.data["positive_signals"])
        self.assertTrue(response.data["red_flags"])
        self.assertIn("repayment_capacity", response.data["score_breakdown"])
        self.assertIn("risk_compliance", response.data["score_breakdown"])
        self.assertTrue(any("AI tidak menyetujui" in reason for reason in response.data["main_reasons"]))

        response = self.client.get(f"/api/borrower-profiles/{profile_id}/audit-logs/")
        self.assertEqual(response.status_code, 200, response.content)
        actions = {log["action"] for log in response.data}
        self.assertIn("CONSENT_RECORDED", actions)
        self.assertIn("SUBMITTED_TO_ANALYST", actions)
        self.assertIn("SUBMISSION_UNDONE", actions)
        self.assertIn("DEEPSCORE_REVIEW_RUN", actions)

        response = self.client.patch(
            f"/api/analyst/reviews/{review_id}/decision/",
            {"final_human_decision": "NEEDS_MORE_DATA", "analyst_notes": "Minta dua bukti transaksi tambahan."},
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.data["final_human_decision"], "NEEDS_MORE_DATA")
        self.assertEqual(BorrowerProfile.objects.get(pk=profile_id).status, "NEEDS_COMPLETION")

        response = self.client.get(f"/api/borrower-profiles/{profile_id}/audit-logs/")
        self.assertEqual(response.status_code, 200, response.content)
        self.assertTrue(any(log["action"] == "HUMAN_DECISION_UPDATED" for log in response.data))

        # Field Agent Mode: 1. Login, 2. Open assisted case
        agent_user = self.login("fieldagent@mitrascore.demo")
        self.assertEqual(agent_user["role"], "FIELD_AGENT")
        response = self.client.get("/api/borrower-profiles/")
        self.assertEqual(response.status_code, 200, response.content)
        self.assertTrue(any(case["id"] == profile_id for case in response.data))

        # 3. Add observation note, 4. Upload or verify evidence, 5. Mark agent-assisted/verified
        business_photo = EvidenceItem.objects.get(borrower_profile_id=profile_id, evidence_type=EvidenceType.BUSINESS_PHOTO)
        response = self.client.patch(
            f"/api/evidence/{business_photo.id}/source-type/",
            {"source_type": "AGENT_VERIFIED", "field_agent_note": "Foto usaha diverifikasi dengan lokasi dan stok saat kunjungan."},
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.data["source_type"], "AGENT_VERIFIED")

        receipt = EvidenceItem.objects.filter(borrower_profile_id=profile_id, evidence_type=EvidenceType.RECEIPT).first()
        response = self.client.patch(
            f"/api/evidence/{receipt.id}/source-type/",
            {"source_type": "AGENT_VERIFIED", "field_agent_note": "Nota pemasok dicocokkan dengan stok dan tanggal transaksi."},
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.data["source_type"], "AGENT_VERIFIED")

        item_id = self.upload_and_process(
            profile_id,
            "agent_verified_supplier_note_e2e.pdf",
            EvidenceType.SUPPLIER_NOTE,
            SourceType.AGENT_ASSISTED,
            "Agen melihat stok barang dan nota pemasok saat kunjungan.",
        )
        response = self.client.patch(
            f"/api/evidence/{item_id}/source-type/",
            {"source_type": "AGENT_VERIFIED", "field_agent_note": "Bukti diverifikasi agen di lokasi usaha."},
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.data["source_type"], "AGENT_VERIFIED")
        self.assertEqual(response.data["field_agent_note"], "Bukti diverifikasi agen di lokasi usaha.")

        # 6. Run Instant Evidence Check again
        response = self.client.post(f"/api/borrower-profiles/{profile_id}/instant-check/", {}, format="json")
        self.assertEqual(response.status_code, 201, response.content)
        self.assertTrue(response.data["can_submit_to_analyst"])

        response = self.client.post(f"/api/borrower-profiles/{profile_id}/submit-to-analyst/", {}, format="json")
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.data["status"], "READY_FOR_ANALYST")
        self.assertEqual(response.data["workflow_stage"]["code"], "ANALYST_QUEUE")

        analyst_user = self.login("analyst@mitrascore.demo")
        self.assertEqual(analyst_user["role"], "ANALYST")
        response = self.client.post(f"/api/analyst/cases/{profile_id}/deepscore/", {}, format="json")
        self.assertEqual(response.status_code, 201, response.content)
        final_review_id = response.data["id"]
        response = self.client.patch(
            f"/api/analyst/reviews/{final_review_id}/decision/",
            {"final_human_decision": "APPROVED_FOR_FINANCING", "analyst_notes": "Data tambahan cukup. Disetujui untuk proses pembiayaan berikutnya."},
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.data["final_human_decision"], "APPROVED_FOR_FINANCING")
        self.assertEqual(BorrowerProfile.objects.get(pk=profile_id).status, "REVIEWED")
