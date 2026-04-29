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

## 2. Seeded Happy Path: Owner To Analyst

Login as `umkm@mitrascore.demo`.

1. Open Owner Dashboard.
2. Confirm Warung Ibu Sari appears.
3. Confirm workflow panel explains the current owner action.
4. Click `Lanjutkan`.
5. Confirm consent is already visible.
6. Review profile fields and evidence list.
7. In evidence list, confirm source badges are understandable:
   - `Self uploaded`: uploaded by owner, no field verification bonus.
   - `Agent assisted`: agent helped collect/upload, no verification claim.
   - `Agent verified`: agent verified context/original document, adds evidence-quality weight.
8. Run `Instant Evidence Check`.
9. Confirm completeness, evidence quality, and recommended next steps are visible.
10. If `Kirim ke analis` is enabled, click it.
11. Confirm workflow moves to analyst queue or waiting-for-analyst state.

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
   - Score breakdown appears.
   - Positive signals and red flags appear.
   - Evidence source meanings/effects are visible.
   - Audit trail includes `SUBMITTED_TO_ANALYST` and `DEEPSCORE_REVIEW_RUN`.

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

1. Set decision to `Setujui untuk proses pembiayaan`.
2. Add note: `Disetujui untuk proses pembiayaan berikutnya setelah review manusia.`
3. Click `Simpan`.

Expected:

1. Owner sees approval for next financing process.
2. Owner still sees this is a human decision, not AI approval.
3. Case status is reviewed/finalized.
4. Audit trail includes the final human decision.

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

1. Owner sees clear rejection and reasons.
2. Owner sees guidance to improve before future submission.
3. Field agent sees only support actions if owner asks for help.
4. Audit trail records the decision.

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
   - Use `Agent assisted - dibantu agen` if the agent only helped collect/upload.
   - Use `Agent verified - diverifikasi agen` only if the agent checked the evidence against observed business context or original documents.
6. For `Agent verified`, add a verification note. Confirm upload is disabled if the note is missing.
7. Confirm the evidence card explains meaning and effect.
8. Run `Check`.
9. Click `Kirim ke Analis` when eligible.

Login as `analyst@mitrascore.demo`.

1. Confirm the case returned to analyst queue.
2. Open the case.
3. Confirm new evidence and agent note are visible.
4. Run `DeepScore` again.
5. Save a final decision, usually `APPROVED_FOR_FINANCING`, `RECOMMENDED_FOR_REVIEW`, or `DECLINED`.
6. Return to owner dashboard and confirm final decision is visible.

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
6. Upload evidence as `Agent assisted`.
7. Upload or mark at least one item as `Agent verified` with a verification note.
8. Run `Check`.
9. Click `Kirim ke Analis` when eligible.

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

1. Upload evidence as `Agent assisted`.
   Expected: card says agent helped collect/upload; no verification bonus.
2. Try changing an item to `Agent verified` without a note.
   Expected: system asks for a verification note.
3. Add note such as:
   `Nota asli dilihat saat kunjungan dan cocok dengan stok barang di warung.`
4. Mark as verified.
   Expected: card says verified; effect says it adds evidence-quality points.
5. Run Instant Evidence Check.
   Expected: evidence quality can improve because verified evidence adds weight.
6. Open Analyst Dashboard.
   Expected: analyst can see source meaning, source effect, and agent note.

## 8. Undo And Deletion Checks

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

## 9. Expected Seeded Case Outcome

Warung Ibu Sari should generally show:

- Score around `70-85`.
- Readiness band around `PROMISING`.
- Confidence `MEDIUM` or `HIGH`, depending on evidence.
- Red flags around informal credit history or collateral if the seeded notes include them.
- Suggested next action around additional transaction proofs and financing-purpose verification.

Exact score can vary slightly after you add or verify evidence.

## 10. Final Acceptance Checklist

A full successful demo should prove:

1. Owner can self-onboard, consent, upload evidence, check readiness, and submit.
2. Owner can request field-agent help.
3. Field agent can assist, verify evidence, explain evidence source status, run check, and submit to analyst.
4. Analyst can run DeepScore and make every human decision type.
5. `NEEDS_MORE_DATA` creates a clear request-response loop back to owner/agent and then back to analyst.
6. `APPROVED_FOR_FINANCING` and `DECLINED` are explicit human decisions.
7. All roles see clear workflow stage, next actions, notes, and audit history.
8. Responsible AI boundary is visible: DeepScore is advisory; final decision is human.

## 11. Reset Demo State Again

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
