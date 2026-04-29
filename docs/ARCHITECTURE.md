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
2. Borrower profile is created or loaded.
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
   - `DECLINED`: human rejection with reviewer notes.
11. Owner and field agent see the decision, reviewer notes, and role-specific follow-up actions.
12. If more data is requested, owner or field agent responds with updated profile data/evidence, reruns Instant Evidence Check, and submits the response back to analyst.

Every borrower profile response includes workflow metadata:

- `status_label`: user-facing status.
- `workflow_stage`: current workflow stage and summary.
- `role_next_actions`: next actions for UMKM owner, field agent, analyst, and admin.

## Scoring

Credit Readiness Score is deterministic and explainable:

- Repayment Capacity: 30%
- Business Consistency: 25%
- Evidence Quality: 20%
- Operational Stability: 15%
- Risk & Compliance Signals: 10%

The score is a readiness signal only, not a financing decision.
Final approve or decline outcomes are explicit human decisions recorded by the analyst and audit logged.
