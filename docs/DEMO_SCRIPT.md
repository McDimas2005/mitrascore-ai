# Demo Script

Use this as a begin-to-end walkthrough and QA checklist for all major MitraScore AI scenarios. The goal is to confirm that each role can clearly see the current workflow stage, the request from the previous role, the expected response, and the next available action.

## 0. Setup And Reset

Start from a clean local demo state when testing the full flow.

```bash
cd apps/api
. .venv/bin/activate
python manage.py migrate
python manage.py reset_local_demo --yes
```

Run the apps:

```bash
cd apps/api
. .venv/bin/activate
python manage.py runserver 0.0.0.0:8000
```

```bash
cd apps/web
npm run dev
```

Open the Next.js URL printed by `npm run dev`.

All demo passwords are `Demo123!`.

- UMKM owner with seeded case: `umkm@mitrascore.demo`
- Blank UMKM owner: `umkm2@mitrascore.demo`
- Field agent: `fieldagent@mitrascore.demo`
- Analyst: `analyst@mitrascore.demo`
- Admin: `admin@mitrascore.demo`

## 1. What To Check On Every Screen

For every role and case, confirm these are visible and understandable:

1. Workflow panel shows the current stage, summary, and next actions for the logged-in role.
2. Status label is user-facing, not only a raw backend code.
3. Any reviewer request or note is visible to the role expected to respond.
4. Available buttons match the current state. Disabled actions should make sense.
5. Audit trail records important transitions such as consent, submit, DeepScore, human decision, evidence updates, and resubmission.
6. Responsible AI message remains clear: AI/DeepScore does not approve or reject financing; the analyst records the human decision.
7. Owner dashboard supports more than one usaha. Each usaha must keep its own evidence, workflow, review result, and next actions.

## 2. Seeded Happy Path: Owner To Analyst

Login as `umkm@mitrascore.demo`.

1. Open Owner Dashboard.
2. Confirm `Daftar usaha` appears and Warung Ibu Sari is selectable.
3. Confirm `Tambah usaha` is available for another business profile.
4. Select Warung Ibu Sari and confirm workflow panel explains the current owner action.
5. Click `Lanjutkan`.
6. Confirm consent is already visible.
7. Review profile fields and evidence list.
8. In evidence list, confirm source badges are understandable:
   - `Unggahan owner`: owner mengunggah sendiri, belum ada bobot verifikasi lapangan.
   - `Dibantu agen`: agen membantu ambil/unggah bukti, tetapi belum menjadi klaim verifikasi.
   - `Diverifikasi agen`: agen mencocokkan bukti dengan konteks usaha atau dokumen asli.
9. Run `Instant Evidence Check`.
10. Confirm completeness, evidence quality, and recommended next steps are visible.
11. If `Kirim ke analis` is enabled, click it.
12. Confirm workflow moves to analyst queue or waiting-for-analyst state.

Login as `analyst@mitrascore.demo`.

1. Open Analyst Dashboard.
2. Confirm the submitted case appears.
3. Select Warung Ibu Sari.
4. Confirm workflow panel tells analyst to run/review DeepScore.
5. Run `DeepScore`.
6. Confirm:
   - Score appears.
   - Readiness band appears.
   - Confidence appears.
   - Verification readiness panel appears.
   - Score breakdown appears.
   - Positive signals and red flags appear.
   - Evidence source badges and agent notes are visible.
   - Audit trail includes `SUBMITTED_TO_ANALYST` and `DEEPSCORE_REVIEW_RUN`.

## 2A. Multiple Business Profiles Per Owner

Use this to confirm one UMKM owner can operate more than one usaha without mixing evidence or decisions.

Login as `umkm@mitrascore.demo`.

1. Open Owner Dashboard.
2. Click `Tambah usaha`.
3. Create a second business profile, for example `Catering Ibu Sari`.
4. Give consent for the second business.
5. Upload evidence for the second business only.
6. Return to Owner Dashboard.
7. Confirm both businesses appear in `Daftar usaha`.
8. Select each business and confirm:
   - Business name, category, workflow, evidence count, check result, and review result are shown for the selected business only.
   - Evidence from Warung Ibu Sari does not appear under Catering Ibu Sari.
   - A final decision on one business does not hide or block another business.
9. Use `Bantuan agen untuk usaha baru` and confirm it creates a separate assisted draft instead of modifying the selected business.
10. If one business is `Ditolak final pada review manusia`, confirm `Tambah usaha` is still available so the owner can start another valid business/application path.

## 3. Analyst Decision Branches

For each branch below, save the decision, then login as owner and field agent to confirm both roles see the result and next actions.

### A. Pending

Analyst:

1. Set decision to `Pending - masih direview`.
2. Add note: `Masih menunggu klarifikasi internal.`
3. Click `Simpan`.

Expected:

1. Analyst sees saved confirmation.
2. Case remains under human review.
3. Owner sees that the reviewer has not finalized the decision yet.
4. Field agent sees no immediate required evidence action unless asked later.

### B. Needs More Data

Analyst:

1. Set decision to `Perlu data tambahan`.
2. Add a clear request, for example:
   `Minta dua bukti transaksi terbaru dan verifikasi tujuan pembiayaan.`
3. Click `Simpan`.

Expected:

1. Case moves to a completion/follow-up state.
2. Owner dashboard shows reviewer note and follow-up actions.
3. Field agent dashboard shows the reviewer request and can help respond.
4. Audit trail includes `HUMAN_DECISION_UPDATED`.

Then continue with Section 4.

### C. Recommended For Review

Analyst:

1. Set decision to `Rekomendasikan review pembiayaan lanjutan`.
2. Add note: `Data cukup untuk review pembiayaan final, namun belum menjadi persetujuan otomatis.`
3. Click `Simpan`.

Expected:

1. Owner sees that the case is recommended for further review.
2. Owner sees next actions to prepare supporting documents and keep contact active.
3. Analyst sees next action to complete final financing review.

### D. Approved For Financing

Analyst:

1. Before selecting approval, check the verification readiness panel.
2. If approval is blocked, confirm the panel explains what is missing:
   - Minimal satu bukti keberadaan usaha yang sudah diverifikasi.
   - At least two verified cashflow or transaction evidence items.
   - Catatan verifikasi pada setiap bukti `Diverifikasi agen`.
3. If blocked, choose `Perlu data tambahan` and request verification by field agent.
4. After the missing evidence is verified, set decision to `Setujui untuk proses pembiayaan`.
5. Add note: `Disetujui untuk proses pembiayaan berikutnya setelah review manusia.`
6. Click `Simpan`.

Expected:

1. Approval cannot be saved while decision-critical evidence is not verified.
2. Owner sees approval for next financing process only after verification readiness is satisfied.
3. Owner still sees this is a human decision, not AI approval.
4. Case status is reviewed/finalized.
5. Audit trail includes the final human decision.

### E. Not Recommended At This Stage

Analyst:

1. Set decision to `Belum direkomendasikan saat ini`.
2. Add note: `Bukti arus kas belum cukup kuat. Perlu riwayat transaksi tambahan.`
3. Click `Simpan`.

Expected:

1. Owner sees improvement steps.
2. Field agent can assist if more evidence or verification is needed.
3. Case is not treated as final loan approval.

### F. Declined

Analyst:

1. Set decision to `Tolak pada review manusia`.
2. Add note: `Ditolak karena bukti transaksi dan kapasitas bayar belum memadai.`
3. Click `Simpan`.

Expected:

1. Owner sees a stricter final rejection state: `Ditolak final pada review manusia`.
2. Owner sees the reviewer reason and a clear message that this application cycle is closed.
3. Owner cannot edit the same profile, upload more evidence, run check again, or submit the same application back to analyst.
4. Field agent cannot change profile data, add evidence, mark evidence as verified, or resubmit this closed case.
5. Analyst sees that the case is final and can only reopen it deliberately with `Buka ulang ke Pending` if the decision must be corrected.
6. Audit trail records the decision.

Negative test for the same declined case:

1. Login as owner and click the closed case if still reachable.
2. Confirm normal correction actions are disabled or blocked by API.
3. Login as field agent and confirm upload, verification, check, and submit actions are disabled or blocked.
4. Do not treat this path like `Belum direkomendasikan saat ini`.

New application path after decline:

1. If policy allows another attempt, start a new application cycle instead of editing the rejected one.
2. Use materially improved evidence, updated business data, and field-agent verification before submitting again.

## 4. Needs-More-Data Response Loop

Use this after Section 3B.

Login as `umkm@mitrascore.demo`.

1. Open Owner Dashboard.
2. Confirm reviewer note is visible.
3. Click `Lanjutkan`.
4. Upload additional evidence if testing owner response.
5. Run `Instant Evidence Check` again.
6. If eligible, click `Kirim ke analis`.
7. Confirm workflow says the response is sent to analyst queue.

Login as `fieldagent@mitrascore.demo` if testing assisted response.

1. Open Field Agent Dashboard.
2. Select the same case.
3. Confirm reviewer note is visible.
4. Upload a new evidence file.
5. Choose source type carefully:
   - Gunakan `Dibantu agen` jika agen hanya membantu mengambil atau mengunggah bukti.
   - Gunakan `Diverifikasi agen` hanya jika agen sudah mencocokkan bukti dengan konteks usaha yang dilihat atau dokumen asli.
6. Untuk `Diverifikasi agen`, isi catatan verifikasi. Pastikan upload tidak bisa dilakukan jika catatan kosong.
7. Confirm the evidence card shows a clear source badge without repeated meaning/effect text.
8. Ensure the anti-scam approval requirements are satisfied:
   - Verifikasi minimal satu bukti keberadaan usaha, biasanya foto usaha.
   - Verifikasi minimal dua bukti arus kas/transaksi, seperti nota, invoice, catatan pemasok, catatan penjualan, atau QRIS.
9. Run `Check`.
10. Click `Kirim ke Analis` when eligible.

Login as `analyst@mitrascore.demo`.

1. Confirm the case returned to analyst queue.
2. Open the case.
3. Confirm new evidence and agent note are visible.
4. Run `DeepScore` again.
5. Confirm the verification readiness panel is approval-ready before choosing `APPROVED_FOR_FINANCING`.
6. Save a final decision, usually `APPROVED_FOR_FINANCING`, `RECOMMENDED_FOR_REVIEW`, or `DECLINED`.
7. Return to owner dashboard and confirm final decision is visible.

## 5. Field-Agent Assistance From Blank Owner

Login as `umkm2@mitrascore.demo`.

1. Open Owner Dashboard.
2. Confirm there is no existing profile.
3. Fill the field-agent request form.
4. Click `Minta Bantuan Agen`.
5. Confirm a draft assisted case is created.

Login as `fieldagent@mitrascore.demo`.

1. Confirm the new assisted case appears.
2. Open it.
3. Confirm visit/request information is visible.
4. Fill or correct profile details.
5. Save changes.
6. Upload evidence as `Dibantu agen`.
7. Upload atau tandai minimal satu bukti keberadaan usaha sebagai `Diverifikasi agen` dengan catatan verifikasi.
8. Upload atau tandai minimal dua bukti arus kas/transaksi sebagai `Diverifikasi agen` dengan catatan verifikasi.
9. Run `Check`.
10. Click `Kirim ke Analis` when eligible.

Login as `analyst@mitrascore.demo`.

1. Confirm the case appears in the analyst queue.
2. Run DeepScore.
3. Save a human decision.
4. Confirm the owner and field agent dashboards reflect the decision and next actions.

## 6. Consent And Permission Checks

Test these with `umkm2@mitrascore.demo` or a freshly reset case.

1. Try uploading evidence before consent.
   Expected: upload/scoring is blocked until consent is given.
2. Give consent.
   Expected: evidence upload and scoring become available.
3. Revoke consent.
   Expected: upload/scoring are blocked again.
4. Login as owner and try to access analyst dashboard directly.
   Expected: permission denied or blocked API response.
5. Login as analyst and try deleting a borrower profile.
   Expected: analyst cannot delete borrower profiles.
6. Login as admin.
   Expected: admin can see analyst dashboard and admin-only delete controls.

## 7. Evidence Source Type Checks

Use the Field Agent Dashboard.

1. Upload evidence as `Dibantu agen`.
   Expected: card says agent helped collect/upload; no verification bonus.
2. Try changing an item to `Diverifikasi agen` without a note.
   Expected: system asks for a verification note.
3. Add note such as:
   `Nota asli dilihat saat kunjungan dan cocok dengan stok barang di warung.`
4. Mark as verified.
   Expected: card says the item is verified and the verification readiness panel updates.
5. Verifikasi minimal satu bukti keberadaan usaha dan dua bukti arus kas/transaksi.
   Expected: verification readiness panel becomes approval-ready.
6. Run Instant Evidence Check.
   Expected: evidence quality can improve because verified evidence adds weight.
7. Open Analyst Dashboard.
   Expected: analyst can see source meaning, source effect, and agent note.

## 8. Anti-Scam Approval Gate Checks

Use Analyst Dashboard after DeepScore exists.

1. Try selecting `Setujui untuk proses pembiayaan` before key evidence is verified.
   Expected: save is blocked and the verification readiness panel explains what is missing.
2. Login as field agent.
3. Tandai satu bukti keberadaan usaha sebagai `Diverifikasi agen` dengan catatan yang jelas.
4. Tandai dua bukti arus kas/transaksi sebagai `Diverifikasi agen` dengan catatan yang jelas.
5. Run `Check` and submit back to analyst.
6. Login as analyst and rerun `DeepScore`.
7. Confirm verification readiness is approval-ready.
8. Save `Setujui untuk proses pembiayaan`.
   Expected: approval succeeds only after verification readiness is satisfied.

## 9. Undo And Deletion Checks

Owner:

1. Submit a case to analyst before DeepScore.
2. Click `Batalkan Kirim`.
3. Expected: case returns to completion/onboarding flow.

After DeepScore exists:

1. Try undoing submission.
2. Expected: undo is blocked because review has been created.

Admin:

1. Login as `admin@mitrascore.demo`.
2. Open Analyst Dashboard.
3. Confirm admin delete control appears.
4. Delete only test/demo cases you intentionally created.

## 10. Expected Seeded Case Outcome

Warung Ibu Sari should generally show:

- Score around `70-85`.
- Readiness band around `PROMISING`.
- Confidence may be `LOW` before field verification, then can rise after key evidence is verified.
- Red flags around informal credit history or collateral if the seeded notes include them.
- Suggested next action around additional transaction proofs and financing-purpose verification.

Exact score can vary slightly after you add or verify evidence.

## 11. Final Acceptance Checklist

A full successful demo should prove:

1. Owner can self-onboard, consent, upload evidence, check readiness, and submit.
2. Owner can request field-agent help.
3. Field agent can assist, verify evidence, explain evidence source status, run check, and submit to analyst.
4. Analyst can run DeepScore and make every human decision type.
5. `NEEDS_MORE_DATA` creates a clear request-response loop back to owner/agent and then back to analyst.
6. `APPROVED_FOR_FINANCING` and `DECLINED` are explicit human decisions.
7. Approval is blocked until decision-critical evidence is agent verified.
8. All roles see clear workflow stage, next actions, notes, verification readiness, and audit history.
9. Responsible AI boundary is visible: DeepScore is advisory; final decision is human.

## 12. Reset Demo State Again

Before repeating the full demo:

```bash
cd apps/api
. .venv/bin/activate
python manage.py reset_local_demo --yes
```

For Docker/Postgres:

```bash
cd apps/api
. .venv/bin/activate
DATABASE_URL=postgres://mitrascore:mitrascore@localhost:5432/mitrascore python manage.py reset_local_demo --yes
```
