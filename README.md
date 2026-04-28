# MitraScore AI

Local MVP for transforming informal UMKM business evidence into an explainable Credit Readiness Score. This demo uses mock Azure-style AI adapters only. It does not require Azure credentials and never automatically approves or rejects financing.

## Apps

- `apps/api`: Django, Django REST Framework, JWT auth, PostgreSQL-ready settings with SQLite fallback for local tests.
- `apps/web`: Next.js, TypeScript, Tailwind CSS mobile-first dashboard.
- `infra`: Docker Compose and environment examples.
- `docs`: architecture, Responsible AI notes, and demo script.

## Quick Start

Backend:

```bash
cd apps/api
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo
python manage.py runserver 0.0.0.0:8000
```

Frontend:

```bash
cd apps/web
npm install
npm run dev
```

Open the Next.js URL printed by `npm run dev`. The frontend calls the API at `http://127.0.0.1:8000/api` by default, and the API allows local dev origins such as `localhost:3000` and `localhost:3001`.

## Demo Users

All demo passwords are `Demo123!`.

- `umkm@mitrascore.demo`
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
DATABASE_URL=postgres://mitrascore:mitrascore@localhost:5432/mitrascore python manage.py migrate
```

## Tests

```bash
cd apps/api
python manage.py test
```

Covered: consent gating, role permissions, completeness scoring, score breakdown, audit logs, and deterministic mock AI extraction.

## Responsible AI Boundaries

- Consent is required before upload and scoring.
- AI does not approve or reject financing.
- No face recognition.
- No protected attribute scoring.
- No social media scraping.
- Important workflow actions are logged in `AuditLog`.
