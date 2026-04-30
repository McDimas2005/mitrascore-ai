# Responsible AI

MitraScore AI is built around human-in-the-loop credit readiness, not automated lending decisions.

The deployed demo should use only synthetic or consented demo evidence. Azure Blob Storage, Azure AI Vision, Azure Document Intelligence, Neon, Azure App Service, and Vercel do not change the core Responsible AI boundary: AI remains decision-support and every final financing decision requires human review.

## Consent-First Design

- Consent must be recorded before evidence upload, OCR, photo analysis, Instant Evidence Check, or DeepScore.
- Consent text explains that AI supports analysis only.
- Users can revoke consent; upload and scoring are blocked until consent is given again.

## Human-In-The-Loop Policy

- DeepScore is decision-support.
- AI never approves or rejects financing.
- Final decisions are recorded by a human analyst.
- Analyst notes are required for final rejection so the owner understands the decision.
- Final approval is blocked until decision-critical evidence is verified by a field agent.

## Data Used

- Business profile data provided by the UMKM owner or field agent.
- Uploaded business evidence.
- Field-agent notes and verification status.
- OCR, document extraction, and business-photo indicators.

## Data Not Used

- Protected or sensitive attributes.
- Face recognition or identity recognition from faces.
- Personal appearance.
- Ethnicity, religion, gender, lifestyle, or home luxury.
- Social media scraping.
- Contacts or unrelated personal data outside uploaded evidence.

## Azure AI Limitation Handling

- Azure AI Vision is used only for business-relevant visual indicators: product/category hints, stock presence, storefront context, signage text, quality flags, and confidence.
- Azure Document Intelligence is used for OCR and document fields: text, transaction amount, date, merchant/supplier text, item-like lines, confidence, and low-quality flags.
- Low confidence, missing fields, unclear images, cropped documents, handwriting, or OCR gaps are surfaced as warnings for human review.
- If Azure credentials are missing or Azure calls fail, the app records failed AI processing and shows a fallback message. Demo mode can continue with `USE_MOCK_AI=true`.

## Audit Trail

The app logs important events:

- Consent recorded.
- Evidence uploaded.
- Azure Blob upload attempted, succeeded, failed, or fell back to local.
- Mock AI processing started/completed.
- Azure Vision processing started/completed.
- Azure Document Intelligence processing started/completed.
- Failed AI processing attempts.
- Instant Evidence Check run.
- DeepScore Review run.
- Human decision updated.
- Evidence source or verification status updated.

## Evidence Verification Gate

Before human approval for the next financing process, the profile must include:

- At least one field-verified business-presence evidence item.
- At least two field-verified cashflow or transaction evidence items.
- A field-agent verification note for every verified evidence item.

If this gate is not met, analyst review can continue, but final approval is blocked.

## Confidence Explanation

- `HIGH`: evidence complete and consistent.
- `MEDIUM`: enough evidence but some uncertainty remains.
- `LOW`: limited or weak evidence.

## Future Monitoring

Production hardening should add:

- Fairness monitoring across permitted, non-sensitive business segments.
- Model drift monitoring for OCR/Vision confidence and extraction quality.
- Human override analysis and appeal tracking.
- Periodic review of red-flag language to avoid proxy discrimination.
- Data retention and deletion workflows for uploaded evidence and Azure analysis results.

## Explicit Prohibitions

- No face recognition.
- No protected attribute scoring.
- No social media scraping.
- No automated approval or rejection.
- No black-box credit model as the source of truth.
