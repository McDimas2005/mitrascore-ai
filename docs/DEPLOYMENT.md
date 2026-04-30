# Deployment Guide

This guide keeps the deployment safe for hackathon and Azure Student credit. Do not require AKS, Kubernetes, GPU, Azure ML compute, Container Apps, Azure PostgreSQL, or Azure AI Search.

## Recommended Setup

- Frontend: Vercel or Azure Static Web Apps.
- Backend: Azure App Service only if a hosted API is needed.
- Database: local PostgreSQL, Supabase, or Neon for demo.
- AI: Azure AI Vision and Azure Document Intelligence only when configured.
- Evidence files: local storage by default, Azure Blob private container optionally.
- Emergency fallback: `USE_MOCK_AI=true`.

## Frontend on Vercel

1. Import the repo.
2. Set root directory to `apps/web`.
3. Set `NEXT_PUBLIC_API_BASE_URL=https://<api-host>/api`.
4. Deploy.

## Frontend on Azure Static Web Apps

1. Create Static Web App from GitHub.
2. App location: `apps/web`.
3. Build command: `npm run build`.
4. Output location: `.next`.
5. Set `NEXT_PUBLIC_API_BASE_URL=https://<api-host>/api`.

## Backend on Azure App Service

1. Create a Linux Python App Service.
2. Configure app settings:
   - `DJANGO_DEBUG=0`
   - `DJANGO_SECRET_KEY=<strong-secret>`
   - `DJANGO_ALLOWED_HOSTS=<api-host>`
   - `CORS_ALLOWED_ORIGINS=https://<frontend-host>`
   - `DATABASE_URL=<postgres-compatible-url>`
   - `USE_MOCK_AI=true` for fallback or `false` for Azure AI mode.
3. Add Azure service environment variables only as App Service secrets.
4. Startup command:

```bash
python manage.py migrate && gunicorn config.wsgi:application --bind 0.0.0.0:8000
```

For the current Dockerfile, local/prod compose can run the Django development server for demo only. Use Gunicorn for a real production backend.

## Azure Resource Checklist

Already prepared services should map like this:

- Azure AI services:
  - Copy endpoint to `AZURE_AI_VISION_ENDPOINT`.
  - Copy key to `AZURE_AI_VISION_KEY`.
  - Used for business photo analysis only.

- Azure AI Document Intelligence:
  - Copy endpoint to `AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT`.
  - Copy key to `AZURE_DOCUMENT_INTELLIGENCE_KEY`.
  - Used for receipt, invoice, QRIS, supplier note, sales note, and text extraction.

- Azure Storage Account:
  - Create a private Blob container.
  - Set `USE_AZURE_BLOB_STORAGE=true`.
  - Set `AZURE_STORAGE_CONNECTION_STRING`.
  - Set `AZURE_STORAGE_CONTAINER_NAME`.
  - Do not enable public blob access for this demo.

## Future Optional Azure Portal Setup

- Azure AI Language or Azure OpenAI:
  - Add only behind optional adapters.
  - Require prompts that forbid automated decisions and sensitive attribute scoring.
  - Keep human review required.

- Azure AI Search:
  - Add only when a clean indexing/search adapter exists.
  - Do not make it required for the MVP.

- Production database:
  - Supabase or Neon is sufficient for demo.
  - Azure Database for PostgreSQL can be added later if budget allows.
