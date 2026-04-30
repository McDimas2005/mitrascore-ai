# MitraScore AI

MitraScore AI transforms informal UMKM business evidence into an explainable Credit Readiness Score. The app is decision-support only: AI helps analyze evidence, while final financing decisions remain human-led.

The local MVP still runs without Azure credentials. `USE_MOCK_AI=true` is the default and safest demo mode. Optional Azure support is available for:

- Azure AI Vision through Azure AI services for business photo analysis.
- Azure AI Document Intelligence for OCR and receipt/invoice/QRIS extraction.
- Azure Blob Storage private container for optional evidence storage.

## Apps

- `apps/api`: Django, Django REST Framework, JWT auth, PostgreSQL-ready settings with SQLite fallback.
- `apps/web`: Next.js, TypeScript, Tailwind CSS dashboard.
- `infra`: Docker Compose, production compose example, and environment examples.
- `docs`: architecture, Responsible AI notes, and demo script.

## Local Mock Setup

Backend:

```bash
cd apps/api
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo_data
USE_MOCK_AI=true USE_AZURE_BLOB_STORAGE=false python manage.py runserver 0.0.0.0:8000
```

Frontend:

```bash
cd apps/web
npm install
npm run dev
```

Open the Next.js URL printed by `npm run dev`. The frontend calls `http://127.0.0.1:8000/api` unless `NEXT_PUBLIC_API_URL` is set.

## Demo Users

All demo passwords are `Demo123!`.

- `umkm@mitrascore.demo`
- `umkm2@mitrascore.demo` fresh UMKM account with no seeded profile
- `fieldagent@mitrascore.demo`
- `analyst@mitrascore.demo`
- `admin@mitrascore.demo`

## Docker Postgres

```bash
cd infra
cp .env.example .env
docker compose up -d db
```

Then run the backend with:

```bash
cd apps/api
DATABASE_URL=postgres://mitrascore:mitrascore@localhost:5432/mitrascore python manage.py migrate
```

## Real Azure Setup

Copy `apps/api/.env.example` or `infra/.env.example`, then set only environment variables. Do not hardcode secrets.

To enable real Azure Vision and Document Intelligence:

```bash
USE_MOCK_AI=false
AZURE_AI_VISION_ENDPOINT=https://<your-ai-services-name>.cognitiveservices.azure.com
AZURE_AI_VISION_KEY=<key>
AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT=https://<your-document-intelligence-name>.cognitiveservices.azure.com
AZURE_DOCUMENT_INTELLIGENCE_KEY=<key>
```

Behavior:

- `USE_MOCK_AI=true`: always uses deterministic mock clients.
- `USE_MOCK_AI=false` with credentials: uses Azure Vision for `BUSINESS_PHOTO` and Document Intelligence for document evidence.
- `USE_MOCK_AI=false` with missing credentials or Azure failure: marks the evidence AI status as failed, records audit logs, and shows a clear fallback message. The app does not crash.

To enable optional private Azure Blob Storage:

```bash
USE_AZURE_BLOB_STORAGE=true
AZURE_STORAGE_CONNECTION_STRING=<storage-connection-string>
AZURE_STORAGE_CONTAINER_NAME=<private-container-name>
```

If Blob env vars are missing or upload fails, the app falls back to local file storage and audit logs the fallback. Public blob URLs are not generated.
When Blob upload succeeds, deployed evidence is referenced by private blob name instead of relying on persistent App Service local media files.

## Environment Variables

- `DATABASE_URL`: PostgreSQL connection string. Omit for local SQLite.
- `SECRET_KEY` or `DJANGO_SECRET_KEY`: required secret for production.
- `DEBUG` or `DJANGO_DEBUG`: use `true`/`1` locally, `false`/`0` in production.
- `ALLOWED_HOSTS` or `DJANGO_ALLOWED_HOSTS`: comma-separated API hosts.
- `CSRF_TRUSTED_ORIGINS`: Vercel and Azure HTTPS origins.
- `CORS_ALLOWED_ORIGINS`: comma-separated frontend origins.
- `CORS_ALLOWED_ORIGIN_REGEXES`: local dev regex origins.
- `DATABASE_SSL_REQUIRE`: set `true` for Neon if the URL does not already include `sslmode=require`.
- `DJANGO_SECURE_SSL_REDIRECT`, `DJANGO_SESSION_COOKIE_SECURE`, `DJANGO_CSRF_COOKIE_SECURE`, `DJANGO_SECURE_HSTS_SECONDS`, `DJANGO_SECURE_HSTS_PRELOAD`: production HTTPS hardening controls.
- `USE_MOCK_AI`: `true` by default.
- `AZURE_AI_VISION_ENDPOINT`, `AZURE_AI_VISION_KEY`: Azure AI services Vision credentials.
- `AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT`, `AZURE_DOCUMENT_INTELLIGENCE_KEY`: Document Intelligence credentials.
- `USE_AZURE_BLOB_STORAGE`: `false` by default.
- `AZURE_STORAGE_CONNECTION_STRING`, `AZURE_STORAGE_CONTAINER_NAME`: private Blob container config.
- `MAX_EVIDENCE_UPLOAD_BYTES`: default `8388608`.
- `ALLOWED_EVIDENCE_EXTENSIONS`: default `jpg,jpeg,png,pdf,txt`.
- `ALLOWED_EVIDENCE_MIME_TYPES`: safe demo MIME allow-list.
- `NEXT_PUBLIC_API_URL`: frontend API origin, for example `https://<app-name>.<region>.azurewebsites.net`.
- `AZURE_LANGUAGE_*`, `AZURE_OPENAI_*`, `AZURE_SEARCH_*`: placeholders for future optional extensions only.

## Tests

```bash
cd apps/api
. .venv/bin/activate
python manage.py test
```

Covered: consent gating, role permissions, completeness scoring, deterministic scoring, mock and Azure adapter selection, missing Azure credentials, file validation, local vs Blob storage selection, audit logs, and end-to-end demo flow.

## Reset Local Demo Data

```bash
cd apps/api
. .venv/bin/activate
python manage.py reset_local_demo --yes
```

By default this deletes local uploaded media under `apps/api/media`. Use `--keep-media` to preserve files. The command is blocked when `DEBUG=False`.

## Deployment

Recommended deployment:

- Frontend: Vercel.
- Backend: Azure App Service Basic B1, Linux, Python runtime.
- Database: Neon PostgreSQL using `DATABASE_URL`.
- Evidence files: Azure Blob private container.
- Emergency fallback: set `USE_MOCK_AI=true`.

Full step-by-step instructions are in [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md).

Backend production notes:

- Set `DEBUG=false`.
- Set a strong `SECRET_KEY`.
- Set `ALLOWED_HOSTS` and `CORS_ALLOWED_ORIGINS` to real deployed domains.
- Keep Azure keys in platform secrets, not in git.
- Keep App Service Always On enabled on the B1 plan.
- Azure startup command: `bash startup.sh`.
- Set Azure App Service `WEBSITES_PORT=8000`.
- First deployment commands: `python manage.py migrate`, `python manage.py collectstatic --noinput`, and `python manage.py seed_demo_data`.

Draft CI workflow is in `.github/workflows/ci.yml`.

## Troubleshooting

- Azure evidence processing fails: confirm `USE_MOCK_AI=false` and both endpoint/key variables are present for the evidence type.
- Demo must continue during Azure outage: set `USE_MOCK_AI=true` and rerun processing.
- Blob upload falls back to local: confirm `USE_AZURE_BLOB_STORAGE=true`, connection string, container name, SDK dependency, and private container permissions.
- CORS errors: add the frontend origin to `CORS_ALLOWED_ORIGINS`.
- Production debug warning: set `DEBUG=false`.

## Responsible AI Boundaries

- Consent is required before upload and scoring.
- AI does not approve or reject financing.
- No face recognition.
- No protected attribute scoring.
- No social media scraping.
- Important workflow actions are logged in `AuditLog`.
