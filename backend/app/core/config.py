from functools import lru_cache
from pathlib import Path

from pydantic import Field, AliasChoices
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "ProjectTrace API"
    app_version: str = "0.1.0"
    api_prefix: str = "/api/v1"
    environment: str = "development"
    debug: bool = Field(default=True, validation_alias=AliasChoices("APP_DEBUG"))
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:5173"])
    jwt_secret_key: str = "projecttrace-dev-secret"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60 * 8

    sqlite_path: str = str(BASE_DIR / "data" / "projecttrace.db")
    file_store_path: str = str(BASE_DIR / "data" / "document_store.json")
    upload_dir_path: str = str(BASE_DIR / "data" / "uploads")

    redis_host: str = "redis"
    redis_port: int = 6379
    redis_password: str = ""

    @property
    def sqlalchemy_database_uri(self) -> str:
        return f"sqlite:///{self.sqlite_path}"

    @property
    def sqlite_dir(self) -> Path:
        return Path(self.sqlite_path).resolve().parent

    @property
    def file_store_dir(self) -> Path:
        return Path(self.file_store_path).resolve().parent

    @property
    def upload_dir(self) -> Path:
        return Path(self.upload_dir_path).resolve()

    @property
    def redis_uri(self) -> str | None:
        if not self.redis_host:
            return None
        credentials = f":{self.redis_password}@" if self.redis_password else ""
        return f"redis://{credentials}{self.redis_host}:{self.redis_port}/0"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
