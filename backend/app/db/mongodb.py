from pathlib import Path

from tinydb import TinyDB
from app.core.config import settings

Path(settings.file_store_dir).mkdir(parents=True, exist_ok=True)

database = TinyDB(settings.file_store_path, ensure_ascii=False, indent=2)
