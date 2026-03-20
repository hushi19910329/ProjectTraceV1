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

## Development storage

Current development mode uses:

- PostgreSQL for relational data (primary)
- file-based TinyDB JSON store for document/extension data
- Redis as optional cache

For automated tests, `pytest` uses an isolated SQLite database to keep tests self-contained.

## Main endpoints

- `GET /api/v1/health`
- `GET /api/v1/meta/modules`
