# Responsible AI

The MVP is built around human-in-the-loop credit readiness, not automated lending decisions.

## Required Controls

- Consent must be recorded before evidence upload or scoring.
- AI output is labeled as assistance for review.
- Analyst screens show data used, data not used, confidence, warnings, and audit logs.
- Final decision field is human-maintained.
- Final approval is blocked until decision-critical evidence is `Diverifikasi agen`.
- Agent verification requires notes explaining what was checked.
- Final rejection closes the current application cycle unless an analyst or admin deliberately reopens it.
- One owner can manage multiple businesses, but each business keeps separate evidence, reviews, and decisions.

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

- Minimal satu bukti keberadaan usaha yang sudah `Diverifikasi agen`.
- Minimal dua bukti arus kas atau transaksi yang sudah `Diverifikasi agen`.
- Catatan verifikasi pada setiap bukti yang ditandai `Diverifikasi agen`.

If this gate is not met, analyst review can continue, but final approval is blocked and the recommended decision should be `NEEDS_MORE_DATA`.

## Human Decision Boundaries

DeepScore is advisory. It can help analysts understand readiness, red flags, and missing evidence, but it does not approve or reject financing.

Human decision behavior:

- `PENDING`: review is still open.
- `NEEDS_MORE_DATA`: owner or field agent can respond with updated evidence or clarification.
- `RECOMMENDED_FOR_REVIEW`: case can proceed to further financing review, but this is not automatic approval.
- `NOT_RECOMMENDED_AT_THIS_STAGE`: case is not ready now, but remains recoverable.
- `APPROVED_FOR_FINANCING`: human approval for the next financing process, allowed only after the anti-scam evidence gate is satisfied.
- `DECLINED`: final rejection for the current application cycle; normal owner/field-agent updates are blocked unless the case is reopened.

## Evidence Source Labels

The product uses Indonesian-facing labels:

- `Unggahan owner`: owner uploaded the evidence without field verification.
- `Dibantu agen`: field agent helped collect or upload evidence, but has not verified it.
- `Diverifikasi agen`: field agent verified the evidence against business context or original documents and wrote a note.

Evidence rows show concise source badges and agent notes. Longer explanations are shown in workflow/support panels where they help users understand the process.

## Limitations

Mock AI services are deterministic and designed for local demos. They are not production OCR or credit models.
