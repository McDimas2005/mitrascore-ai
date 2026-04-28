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
4. Evidence is uploaded and processed by mock AI services.
5. Instant Evidence Check determines data sufficiency.
6. Eligible cases are submitted to analyst queue.
7. Analyst runs DeepScore Review and records a human decision.

## Scoring

Credit Readiness Score is deterministic and explainable:

- Repayment Capacity: 30%
- Business Consistency: 25%
- Evidence Quality: 20%
- Operational Stability: 15%
- Risk & Compliance Signals: 10%

The score is a readiness signal only, not a financing decision.
