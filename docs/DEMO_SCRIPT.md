# Demo Script

Use this for a 2 to 3 minute hackathon demo and quick QA walkthrough.

## Setup

```bash
cd apps/api
. .venv/bin/activate
python manage.py migrate
python manage.py reset_local_demo --yes
USE_MOCK_AI=true USE_AZURE_BLOB_STORAGE=false python manage.py runserver 0.0.0.0:8000
```

```bash
cd apps/web
npm run dev
```

All demo passwords are `Demo123!`.

- UMKM owner: `umkm@mitrascore.demo`
- Blank UMKM owner: `umkm2@mitrascore.demo`
- Field agent: `fieldagent@mitrascore.demo`
- Analyst: `analyst@mitrascore.demo`
- Admin: `admin@mitrascore.demo`

## Pitch Track

“MitraScore AI helps informal Indonesian UMKM turn everyday business evidence into an explainable Credit Readiness Score.

Many small businesses do not have formal financial statements, but they do have business photos, receipts, QRIS screenshots, supplier notes, and field-agent observations. MitraScore uses Azure AI Vision to analyze business photos, Azure Document Intelligence to extract OCR from receipts, invoices, and QRIS evidence, and optional Azure Blob Storage to keep uploaded evidence in a private container.

The important boundary is Responsible AI: this is decision-support, not an automated financing decision. The app excludes protected attributes, does not use face recognition, does not scrape social media, and always requires a human analyst for the final decision.

For the hackathon demo we keep mock mode as an emergency fallback with `USE_MOCK_AI=true`. When Azure credentials are configured, the same upload flow can switch to real Azure Vision and Document Intelligence without changing the user experience.”

## Flow

1. Landing page
   - Show the demo/Azure mode banner.
   - Point out the Azure-powered workflow and “Best Use of Microsoft Tech” explanation.

2. UMKM Self-Onboarding
   - Login as `umkm2@mitrascore.demo`.
   - Create a business profile.
   - Confirm the consent-first message.
   - Accept consent.
   - Fill business category, duration, financing purpose, revenue, expense, and cashflow note.

3. Evidence upload
   - Upload a business photo, receipt/invoice, QRIS screenshot, or text sales note.
   - Show accepted file types: jpg, jpeg, png, pdf, txt.
   - Show whether storage is local or Azure Blob private storage.
   - In mock mode, evidence processes deterministically.
   - In Azure mode, business photos use Azure AI Vision and documents use Azure Document Intelligence.

4. Instant Evidence Check
   - Run the check.
   - Show completeness, evidence quality, detected indicators, OCR summary, and recommended next steps.
   - If sufficient, click `Kirim ke analis`.

5. Optional Assisted Field Agent Mode
   - Login as `fieldagent@mitrascore.demo`.
   - Open the assisted case.
   - Add or verify evidence.
   - Use `Diverifikasi agen` only when the agent checked the business context or original document and wrote a verification note.

6. Analyst DeepScore Review
   - Login as `analyst@mitrascore.demo`.
   - Open the submitted case.
   - Run `DeepScore`.
   - Show Credit Readiness Score, score breakdown, confidence explanation, data used, data not used, red flags, positive signals, and verification readiness.

7. Responsible AI Panel
   - Show consent status, explicit non-use of protected attributes, no face recognition, no social media scraping, and model limitations.
   - Read the warning: “AI hanya mendukung analisis. Keputusan akhir pembiayaan tetap dilakukan oleh analis manusia.”

8. Human-led final decision
   - Choose `Perlu data tambahan`, `Direkomendasikan untuk review lanjutan`, or another human decision.
   - If trying approval before verification readiness is complete, show that the API blocks it.
   - Explain the audit trail records consent, uploads, AI processing, Blob attempts, checks, DeepScore, and human decision updates.

## Emergency Fallback

If Azure calls fail during the demo:

```bash
USE_MOCK_AI=true
```

Restart the API and rerun evidence processing. The local MVP remains stable without Azure credentials.

## QA Checks

- Owner cannot view another owner’s data.
- Field agent can only assist assigned or created cases.
- Analyst sees only submitted/reviewed cases.
- Consent is required before upload and scoring.
- Unsafe file extensions are rejected.
- Failed Azure processing does not crash the UI.
- The UI never attributes final financing decisions to AI.
