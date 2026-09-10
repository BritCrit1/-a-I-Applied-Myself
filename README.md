# a-I-Applied-Myself

An AI-powered personal job application agent. Users create an account, upload a resume, confirm a structured candidate profile, define job-search preferences, and authorize an agent to discover, score, track, and eventually apply to suitable jobs.

This repository starts with Milestone 1: the production foundation. External providers such as LLMs, Manus, Gmail, job boards, and schedulers are intentionally isolated behind replaceable interfaces.

## Technology Decisions

- **Django monolith**: keeps operating cost low while providing authentication, ORM, migrations, file uploads, admin, forms, and tests without a large dependency graph.
- **Relational data model**: application state, audit history, deduplication keys, and user-owned profile data fit relational storage. SQLite is used for local development; PostgreSQL can be configured with `DATABASE_URL` in production.
- **Server-rendered UI first**: Milestone 1 prioritizes secure workflows and data integrity over visual polish. A richer frontend can be added once product behavior is stable.
- **Provider interfaces before integrations**: LLM, resume parsing, browser automation, job discovery, Gmail, and scheduling are interfaces/adapters so no single vendor becomes the core architecture.
- **Deterministic code for deterministic work**: scheduling arithmetic, state transitions, permissions, validation, timestamps, retry counters, and deduplication are ordinary application code, not LLM calls.
- **Schema-validated AI boundaries**: provider results must be validated before persistence or action. Stub providers return structured data with the same contracts expected from production adapters.

## Milestones

1. Application skeleton, environment configuration, database schema, authentication foundation, resume upload/storage, resume parsing abstraction, candidate profile, search preferences, provider interfaces, tests, and setup docs.
2. Job discovery abstraction, normalized job model, deduplication, match scoring, application ledger, and job/application dashboard.
3. Manus adapter, task queue, application workflow, approval gates, retries, and failure handling.
4. Gmail integration, correspondence classification, application state updates, and follow-up scheduler.
5. Production hardening, observability, security review, integration tests, and deployment.

## Local Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
python manage.py migrate
python manage.py runserver
```

Open `http://127.0.0.1:8000/`.

## Tests

```powershell
python manage.py test
```

## Configuration

Environment variables are loaded from the shell. `.env.example` documents the expected values, but the application does not automatically load `.env` files in production.

Required in production:

- `DJANGO_SECRET_KEY`
- `DJANGO_ALLOWED_HOSTS`
- `DATABASE_URL`

Optional provider configuration:

- `LLM_PROVIDER`
- `MANUS_API_BASE_URL`
- `MANUS_API_KEY`
- `GMAIL_CLIENT_ID`
- `GMAIL_CLIENT_SECRET`

Never commit API keys, OAuth secrets, Manus credentials, Gmail tokens, or provider credentials.
# Android and Google Cloud

The Android app is named **AIAMS**. See [Android release setup](docs/ANDROID_RELEASE.md)
for APK/AAB builds and the USD 4.99 weekly subscription with a seven-day trial.
See [Google Cloud deployment](docs/GOOGLE_CLOUD.md) for Cloud Run, Cloud SQL,
private resume storage and HTTPS configuration. Real Play purchases and a public
release require external account configuration and completed production features.
