# Deployment Guide: Azure App Service B1 + Vercel + Neon

This guide targets the exact demo architecture:

- Backend: Azure App Service Basic B1, Linux, Python runtime.
- Frontend: Vercel.
- Database: Neon PostgreSQL.
- File storage: Azure Blob Storage private container.
- AI: Azure AI Vision and Azure Document Intelligence, with mock fallback.
- Emergency fallback: `USE_MOCK_AI=true`.

Do not deploy AKS, Kubernetes, GPU, Azure ML compute, Container Apps, Azure AI Search, Azure AI Language, Azure OpenAI, or Azure PostgreSQL for this demo unless the scope changes.

## 1. Neon PostgreSQL

1. Create a Neon project and database.
2. Copy the pooled connection string when available. It usually looks like:

```text
postgresql://<user>:<password>@<pooled-host>/<db>?sslmode=require
```

3. Save it only as the Azure App Service `DATABASE_URL` setting.
4. Do not commit the URL.

Notes:

- Neon requires SSL. Keep `sslmode=require` in the URL.
- The backend also supports `DATABASE_SSL_REQUIRE=true` if a URL does not include SSL mode.
- Run migrations after the App Service is deployed.

## 2. Azure App Service B1 Backend

Create a Linux App Service with Python 3.12 runtime on the Basic B1 pricing plan. B1 is appropriate for a more stable demo because Always On is available, but do not rely on local App Service storage for uploaded evidence; use Azure Blob Storage.

Recommended platform settings:

```text
Runtime stack: Python 3.12
Pricing plan: Basic B1
Always On: On
HTTPS Only: On
Remote build/Oryx: SCM_DO_BUILD_DURING_DEPLOYMENT=true
Startup command: gunicorn config.wsgi:application --bind=0.0.0.0:8000 --timeout 600
```

### App Service Settings

Set these in Azure Portal > App Service > Environment variables:

```text
DEBUG=false
SECRET_KEY=<strong-random-secret>
ALLOWED_HOSTS=<app-name>.azurewebsites.net
CSRF_TRUSTED_ORIGINS=https://<frontend-domain>.vercel.app,https://<app-name>.azurewebsites.net
CORS_ALLOWED_ORIGINS=https://<frontend-domain>.vercel.app
DATABASE_URL=<Neon pooled PostgreSQL URL>
DATABASE_SSL_REQUIRE=true

USE_MOCK_AI=true
USE_AZURE_BLOB_STORAGE=true
AZURE_STORAGE_CONNECTION_STRING=<storage-connection-string>
AZURE_STORAGE_CONTAINER_NAME=<private-container-name>

AZURE_AI_VISION_ENDPOINT=https://<your-ai-services-name>.cognitiveservices.azure.com
AZURE_AI_VISION_KEY=<key>
AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT=https://<your-document-intelligence-name>.cognitiveservices.azure.com
AZURE_DOCUMENT_INTELLIGENCE_KEY=<key>

MAX_EVIDENCE_UPLOAD_BYTES=8388608
ALLOWED_EVIDENCE_EXTENSIONS=jpg,jpeg,png,pdf,txt
ALLOWED_EVIDENCE_MIME_TYPES=image/jpeg,image/png,application/pdf,text/plain,application/octet-stream
```

Optional security settings:

```text
DJANGO_SECURE_SSL_REDIRECT=1
DJANGO_SESSION_COOKIE_SECURE=1
DJANGO_CSRF_COOKIE_SECURE=1
DJANGO_SECURE_HSTS_SECONDS=31536000
DJANGO_SECURE_HSTS_PRELOAD=true
```

### Startup Command

Use the actual Django project module `config`:

```bash
gunicorn config.wsgi:application --bind=0.0.0.0:8000 --timeout 600
```

If you need a one-time migration during setup, run it from SSH/Kudu instead of putting migrations permanently into the startup command.

### GitHub Actions Deployment

The backend deployment workflow is `.github/workflows/master_app-mitrascore-api-demo.yml`.

It intentionally:

- works from `apps/api`, where `requirements.txt` and `manage.py` live;
- runs backend tests before deployment;
- runs `collectstatic` so Django admin/static assets are packaged;
- deploys only the API folder to Azure App Service;
- supports either `AZURE_WEBAPP_PUBLISH_PROFILE` or the Azure-generated publish profile secret already created by Deployment Center.

Recommended GitHub secret:

```text
AZURE_WEBAPP_PUBLISH_PROFILE=<downloaded Azure App Service publish profile XML>
```

The current App Service name in the workflow is:

```text
app-mitrascore-api-demo
```

If the Azure app name changes, update `AZURE_WEBAPP_NAME` in that workflow.

### Install and Build

Azure App Service should install dependencies from:

```text
apps/api/requirements.txt
```

The required deployment packages are already listed there: `gunicorn`, `whitenoise`, `dj-database-url`, `psycopg2-binary`, `django-cors-headers`, and `azure-storage-blob`. Azure Vision and Document Intelligence calls use the existing lightweight REST adapters, so no extra AI SDK package is required for this implementation.

If deploying from repo root, set the build/deploy path to `apps/api` or configure your pipeline to deploy that folder.

### Static Files

WhiteNoise is configured. Run:

```bash
python manage.py collectstatic --noinput
```

The API does not depend heavily on static files, but admin/static assets work with `STATIC_ROOT` and WhiteNoise.

### Migrations and Demo Seed

Run after first deployment:

```bash
python manage.py migrate
python manage.py seed_demo_data
```

`seed_demo_data` is idempotent and creates/updates:

- `umkm@mitrascore.demo` / `Demo123!`
- `umkm2@mitrascore.demo` / `Demo123!`
- `fieldagent@mitrascore.demo` / `Demo123!`
- `analyst@mitrascore.demo` / `Demo123!`
- `admin@mitrascore.demo` / `Demo123!`
- Warung Ibu Sari starter case.

## 3. Azure Blob Storage

1. Create a Storage Account.
2. Create a Blob container.
3. Keep the container private.
4. Set:

```text
USE_AZURE_BLOB_STORAGE=true
AZURE_STORAGE_CONNECTION_STRING=<connection-string>
AZURE_STORAGE_CONTAINER_NAME=<private-container-name>
```

The app does not generate public blob URLs. Uploads are validated by file size, extension, and MIME type before processing.
When Blob upload succeeds, the database stores the private blob name and the app does not depend on persistent App Service local media storage for that evidence.

## 4. Azure AI Services

For real AI mode:

```text
USE_MOCK_AI=false
AZURE_AI_VISION_ENDPOINT=...
AZURE_AI_VISION_KEY=...
AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT=...
AZURE_DOCUMENT_INTELLIGENCE_KEY=...
```

For demo safety or outage fallback:

```text
USE_MOCK_AI=true
```

If Azure processing fails, evidence gets a failed-processing state and audit log entry instead of crashing the app.

## 5. Vercel Frontend

1. Import the GitHub repo into Vercel.
2. Set root directory: `apps/web`.
3. Framework preset: Next.js.
4. Build command: `npm run build`.
5. Install command: `npm ci`.
6. Output: default Vercel Next.js output.
7. Set environment variable:

```text
NEXT_PUBLIC_API_URL=https://<app-name>.azurewebsites.net
```

The frontend appends `/api` internally. Do not include secrets in Vercel env vars. After the first production deployment, copy the Vercel production URL into the Azure CORS and CSRF settings.

## 6. CORS and CSRF

After Vercel deployment, copy the Vercel domain into Azure App Service:

```text
CORS_ALLOWED_ORIGINS=https://<frontend-domain>.vercel.app
CSRF_TRUSTED_ORIGINS=https://<frontend-domain>.vercel.app,https://<app-name>.azurewebsites.net
ALLOWED_HOSTS=<app-name>.azurewebsites.net
```

For a custom domain, add it to the same settings.

## 7. Smoke Test Checklist

Backend:

```bash
curl https://<app-name>.azurewebsites.net/api/health/
curl https://<app-name>.azurewebsites.net/api/runtime-status/
```

Expected:

- `/api/health/` returns `status`, `app`, `environment`, `mock_ai_mode`, `blob_mode`, and `database_reachable`.
- The endpoint returns HTTP 200 even when status is `degraded`, so you can inspect the JSON during Neon cold starts or credential issues.
- `database_reachable` is `true`.
- `blob_mode` is `azure_blob` when Blob settings are enabled.

Frontend:

1. Open Vercel URL.
2. Confirm mode banner loads.
3. Login as `umkm2@mitrascore.demo`.
4. Create business profile.
5. Give consent.
6. Upload jpg/png/pdf/txt evidence.
7. Run Instant Evidence Check.
8. Submit to analyst.
9. Login as analyst and run DeepScore.
10. If approval is blocked, click `Minta verifikasi agen`.
11. Login as field agent and confirm the case appears.

## 8. Rollback and Fallback

- Azure AI outage: set `USE_MOCK_AI=true`, restart App Service, rerun evidence processing.
- Blob issue: set `USE_AZURE_BLOB_STORAGE=false` only for local/emergency debugging. For App Service B1, restore Blob as soon as possible because local App Service storage is not the production evidence store.
- Bad deploy: use Azure App Service deployment center rollback or redeploy the previous commit.
- Database issue: verify Neon is active, pooled URL is correct, and SSL mode is required.

## 9. Local Development Still Works

```bash
cd infra
cp .env.example .env
docker compose up -d db
```

```bash
cd apps/api
. .venv/bin/activate
DATABASE_URL=postgres://mitrascore:mitrascore@localhost:5432/mitrascore DATABASE_SSL_REQUIRE=false USE_MOCK_AI=true USE_AZURE_BLOB_STORAGE=false python manage.py runserver 0.0.0.0:8000
```

```bash
cd apps/web
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000 npm run dev
```
