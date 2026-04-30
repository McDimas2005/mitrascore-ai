# Architecture

MitraScore AI is a monorepo with a DRF API and a Next.js web client.

## Backend

Apps:

- `accounts`: custom email-based user model with `UMKM_OWNER`, `FIELD_AGENT`, `ANALYST`, and `ADMIN` roles.
- `borrowers`: borrower profiles, consent records, onboarding, analyst case views.
- `evidence`: evidence uploads, source types, extraction results.
- `scoring`: Instant Evidence Check and Credit Readiness Review.
- `audit`: immutable-style workflow logs.
- `ai_services`: deterministic mock clients that mirror Azure Vision, Document Intelligence, Language, and Search responsibilities.

## Flow

1. User logs in with JWT.
2. Borrower profile is created or loaded. One UMKM owner can have multiple business profiles; each profile keeps separate evidence, checks, reviews, and final decisions.
3. Consent is recorded before evidence upload or scoring.
4. UMKM owner uploads evidence directly, or requests field-agent assistance.
5. Field agent can create assisted cases, upload evidence, mark evidence as assisted or verified, and submit the response back to the analyst queue.
6. Evidence is uploaded and processed by mock AI services.
7. Instant Evidence Check determines data sufficiency.
8. Eligible cases are submitted to analyst queue.
9. Analyst runs DeepScore Review. This moves the case to `UNDER_REVIEW` until a human decision is saved.
10. Analyst records a human decision:
   - `PENDING`: keep the case under human review.
   - `NEEDS_MORE_DATA`: return the case to owner or field agent for more evidence.
   - `RECOMMENDED_FOR_REVIEW`: move the case to final financing review.
   - `APPROVED_FOR_FINANCING`: human approval for the next financing process.
   - `NOT_RECOMMENDED_AT_THIS_STAGE`: not ready yet; owner can improve and reapply.
   - `DECLINED`: final human rejection for the current application cycle. Normal owner/field-agent correction, evidence upload, check rerun, and resubmission are locked unless the case is deliberately reopened.
11. Owner and field agent see the decision, reviewer notes, and role-specific follow-up actions.
12. If more data is requested, owner or field agent responds with updated profile data/evidence, reruns Instant Evidence Check, and submits the response back to analyst.

Every borrower profile response includes workflow metadata:

- `status_label`: user-facing status.
- `workflow_stage`: current workflow stage and summary.
- `role_next_actions`: next actions for UMKM owner, field agent, analyst, and admin.

## Owner Portfolio

An `UMKM_OWNER` account can manage multiple business profiles. The owner dashboard displays a `Daftar usaha` portfolio list, and selecting a business changes the visible workflow, evidence count, check result, review decision, and next actions for that business only.

Important behavior:

- Evidence, Instant Evidence Check, DeepScore Review, analyst notes, and final decision are scoped to one business profile.
- A final decision on one business does not block the owner's other businesses.
- If one business is `DECLINED`, the owner can still create another business profile with `Tambah usaha`.
- Field-agent assistance can target the selected business or create a separate assisted draft for a new business.

## Evidence Source Types

Evidence items have source labels that are visible in Bahasa Indonesia:

- `SELF_UPLOADED` / `Unggahan owner`: owner uploaded the evidence directly. It can support completeness and OCR, but it is not field-verified.
- `AGENT_ASSISTED` / `Dibantu agen`: field agent helped collect or upload evidence. This records assistance, but is not a verification claim.
- `AGENT_VERIFIED` / `Diverifikasi agen`: field agent checked the evidence against observed business context or original documents. A verification note is required.

The app avoids repeating long meaning/effect text under every evidence row. Detailed meaning is shown where it helps the workflow, while evidence rows use concise badges and agent notes.

## Anti-Scam Approval Gate

Analyst review can happen with unverified evidence, but final approval cannot.

Before `APPROVED_FOR_FINANCING`, the profile must have:

- Minimal satu bukti keberadaan usaha yang sudah `Diverifikasi agen`.
- Minimal dua bukti arus kas atau transaksi yang sudah `Diverifikasi agen`.
- Catatan verifikasi pada setiap bukti yang ditandai `Diverifikasi agen`.

If this gate is not satisfied, the API blocks final approval and returns verification-readiness details. The analyst should choose `NEEDS_MORE_DATA` or another non-approval decision until the missing verification is completed.

## Final Rejection Lock

`DECLINED` is stricter than `NOT_RECOMMENDED_AT_THIS_STAGE`.

- `NOT_RECOMMENDED_AT_THIS_STAGE` is recoverable: owner or field agent can improve data and submit again.
- `DECLINED` closes the current application cycle: normal profile edits, evidence changes, check reruns, resubmission, and same-case field-agent assistance are blocked.
- Analyst or admin can deliberately reopen a declined case by moving the human decision back to `PENDING` when a correction or official reopening is required.

## Scoring

Credit Readiness Score is deterministic and explainable:

- Repayment Capacity: 30%
- Business Consistency: 25%
- Evidence Quality: 20%
- Operational Stability: 15%
- Risk & Compliance Signals: 10%

The score is a readiness signal only, not a financing decision.
Final approve or decline outcomes are explicit human decisions recorded by the analyst and audit logged.
