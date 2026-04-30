# Responsible AI

The MVP is built around human-in-the-loop credit readiness, not automated lending decisions.

## Required Controls

- Consent must be recorded before evidence upload or scoring.
- AI output is labeled as assistance for review.
- Analyst screens show data used, data not used, confidence, warnings, and audit logs.
- Final decision field is human-maintained.
- Final approval is blocked until decision-critical evidence is agent verified.
- Agent verification requires notes explaining what was checked.

## Explicit Non-Use

The MVP does not use:

- Sensitive or protected attributes.
- Face recognition.
- Social media scraping.
- Contacts or unrelated personal data.
- Black-box model scoring.

## Auditability

Important actions are logged:

- Profile created or updated.
- Consent recorded.
- Evidence uploaded and processed.
- Instant Evidence Check run.
- DeepScore Review run.
- Human decision updated.
- Evidence source or verification status updated.

## Anti-Scam Evidence Gate

DeepScore can screen self-uploaded or assisted evidence, but unverified evidence is not approval-grade evidence.

Before `APPROVED_FOR_FINANCING`, the case must include:

- Minimal satu bukti keberadaan usaha yang diverifikasi agen.
- At least two agent-verified cashflow or transaction evidence items.
- Verification notes on every agent-verified evidence item.

If this gate is not met, analyst review can continue, but final approval is blocked and the recommended decision should be `NEEDS_MORE_DATA`.

## Limitations

Mock AI services are deterministic and designed for local demos. They are not production OCR or credit models.
