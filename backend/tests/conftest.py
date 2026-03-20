import os
from pathlib import Path


TEST_DB_PATH = Path(__file__).resolve().parent / "test_projecttrace.db"
os.environ.setdefault("DATABASE_URL", f"sqlite:///{TEST_DB_PATH}")
