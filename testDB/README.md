# testDB

Database/service smoke tests for local development:

- PostgreSQL: `test_postgresql.py`
- MongoDB: `test_mongodb.py`
- MinIO: `test_minio.py`
- Run all: `run_all.py`

## Run

```bash
python testDB/run_all.py
```

Or run one by one:

```bash
python testDB/test_postgresql.py
python testDB/test_mongodb.py
python testDB/test_minio.py
```

## Environment variables

PostgreSQL:

- `PG_HOST` (default: `127.0.0.1`)
- `PG_PORT` (default: `5432`)
- `PG_USER` (default: `postgres`)
- `PG_PASSWORD` (default: `postgres`)
- `PG_DB` (default: `postgres`)
- `PG_SSLMODE` (default: `disable`)

MongoDB:

- `MONGO_HOST` (default: `127.0.0.1`)
- `MONGO_PORT` (default: `27017`)
- `MONGO_URI` (default: `mongodb://127.0.0.1:27017`)
- `MONGO_DB` (default: `admin`)

MinIO:

- `MINIO_HOST` (default: `127.0.0.1`)
- `MINIO_PORT` (default: `9000`)
- `MINIO_CONSOLE_PORT` (default: `9001`)
- `MINIO_SCHEME` (default: `http`)

## Notes

- PostgreSQL driver check requires `psycopg` or `psycopg2`.
- MongoDB driver check requires `pymongo`.
- If drivers are missing, scripts still run socket checks and return `WARN` for query checks.
