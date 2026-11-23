"""Runtime configuration. Every cloud-specific value comes from environment variables (ADR 0007)."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="DRIPLYTICS_", env_file=".env", extra="ignore")

    env: str = "local"
    log_level: str = "INFO"

    database_url: str = "postgresql://driplytics:driplytics-dev@localhost:5432/driplytics"
    redis_url: str = "redis://localhost:6379/0"

    # Object storage through fsspec: s3:// for MinIO/S3, gs:// for Google Cloud Storage.
    storage_protocol: str = "s3"
    storage_endpoint_url: str | None = "http://localhost:9000"  # None = the cloud provider's default
    storage_key: str | None = "driplytics"
    # Local-dev default only; every deployed environment sets DRIPLYTICS_STORAGE_SECRET.
    storage_secret: str | None = "driplytics-dev-secret"  # noqa: S105
    raw_bucket: str = "driplytics-raw"
    data_bucket: str = "driplytics-data"
    # Local dev only: create missing buckets on the readiness check (ADR 0017). Never on in cloud envs.
    storage_auto_create_buckets: bool = False

    readiness_timeout_s: float = 3.0


@lru_cache
def get_settings() -> Settings:
    return Settings()
