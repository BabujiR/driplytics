from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic_settings import BaseSettings, SettingsConfigDict


class WorkerConfig(BaseSettings):
    """Same DRIPLYTICS_* variables as the API, so one .env / compose block configures both."""

    model_config = SettingsConfigDict(env_prefix="DRIPLYTICS_", env_file=".env", extra="ignore")

    env: str = "local"
    log_level: str = "INFO"
    redis_url: str = "redis://localhost:6379/0"
    max_jobs: int = 4
    job_timeout_s: int = 3600

    # Runtime role (row-level security applies), never the owner role (ADR 0003)
    database_url: str = "postgresql://driplytics_app:driplytics-app-dev@localhost:5432/driplytics"

    storage_protocol: str = "s3"
    storage_endpoint_url: str | None = "http://localhost:9000"
    storage_key: str | None = "driplytics"
    storage_secret: str | None = "driplytics-dev-secret"  # noqa: S105 - local-dev default only
    raw_bucket: str = "driplytics-raw"
    data_bucket: str = "driplytics-data"

    import_chunk_rows: int = 2_000_000

    def storage_options(self) -> dict[str, Any] | None:
        if self.storage_protocol != "s3":
            return None
        opts: dict[str, Any] = {"key": self.storage_key, "secret": self.storage_secret}
        if self.storage_endpoint_url:
            opts["client_kwargs"] = {"endpoint_url": self.storage_endpoint_url}
        return opts

    def object_url(self, bucket: str, key: str) -> str:
        if self.storage_protocol == "file":  # tests/offline: buckets are local folders, keys are paths
            return str(Path(bucket, *key.split("/")))
        return f"{self.storage_protocol}://{bucket}/{key}"


@lru_cache
def get_config() -> WorkerConfig:
    return WorkerConfig()
