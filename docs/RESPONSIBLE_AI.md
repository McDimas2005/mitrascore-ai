# Responsible AI

The MVP is built around human-in-the-loop credit readiness, not automated lending decisions.

## Required Controls

- Consent must be recorded before evidence upload or scoring.
- AI output is labeled as assistance for review.
- Analyst screens show data used, data not used, confidence, warnings, and audit logs.
- Final decision field is human-maintained.

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

## Limitations

Mock AI services are deterministic and designed for local demos. They are not production OCR or credit models.
