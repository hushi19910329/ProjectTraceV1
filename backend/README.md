# Backend

FastAPI backend skeleton for ProjectTrace.

## Run locally

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Also supported for quick local testing:

```bash
cd app
python main.py
```

Recommended working directory is `backend/`, not `backend/app/`, when using `uvicorn`.

## Environment config

1. Copy `backend/.env.example` to `backend/.env`.
2. Fill your local credentials (especially `DB_PASSWORD`, `PG_PASSWORD`, `JWT_SECRET_KEY`).
3. Current local PostgreSQL account example:
   - `DB_USER=postgres`
   - `DB_PASSWORD=Admin2023!`

## Development storage

Current development mode uses:

- PostgreSQL for relational data (primary)
- file-based TinyDB JSON store for document/extension data
- Redis as optional cache

For automated tests, `pytest` uses an isolated SQLite database to keep tests self-contained.

## Main endpoints

- `GET /api/v1/health`
- `GET /api/v1/meta/modules`
- `POST /api/v1/projects/{project_id}/tasks/{task_id}/status-updates` (append task/subtask status update history)

## Seed demo data

```bash
python scripts/seed_demo_data.py --reset
```

This seeds demo projects, tasks (including subtasks), comments, mentions, notifications, and operation logs.
