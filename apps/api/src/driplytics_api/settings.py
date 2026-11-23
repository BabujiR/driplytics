"""Runtime configuration. Every cloud-specific value comes from environment variables (ADR 0007)."""

from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="DRIPLYTICS_", env_file=".env", extra="ignore")

    env: str = "local"
    log_level: str = "INFO"

    # Runtime role: never superuser, never BYPASSRLS (ADR 0003). Must be named driplytics_app.
    database_url: str = "postgresql://driplytics_app:driplytics-app-dev@localhost:5432/driplytics"
    # Owner/admin role for migrations and provisioning only. Never used to serve requests.
    migration_database_url: str = "postgresql://driplytics:driplytics-dev@localhost:5432/driplytics"
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
    # Browser-facing S3 endpoint used to sign upload URLs (inside Docker the API reaches MinIO as
    # http://minio:9000, but the browser needs http://localhost:9000). None = storage_endpoint_url.
    # Google Cloud Storage: S3-interoperable endpoint https://storage.googleapis.com + HMAC keys (ADR 0007).
    storage_public_endpoint_url: str | None = None
    storage_region: str = "us-east-1"
    upload_url_expiry_s: int = 3600
    max_upload_bytes: int = 20 * 1024**3  # 20 GB per file

    # Background jobs (Arq on Redis, ADR 0006)
    queue_name: str = "arq:queue"

    readiness_timeout_s: float = 3.0

    # OIDC (ADR 0004). Locally: Keycloak. Tokens must come from this issuer and one of these clients.
    oidc_issuer: str = "http://localhost:8080/realms/driplytics"
    oidc_jwks_url: str | None = None  # default: <issuer>/protocol/openid-connect/certs (Keycloak layout)
    oidc_client_ids: list[str] = ["driplytics-web"]
    oidc_audience: str | None = None
    oidc_leeway_s: int = 30

    def storage_options(self) -> dict[str, Any] | None:
        """fsspec options for the configured object store (None for local files)."""
        if self.storage_protocol != "s3":
            return None
        opts: dict[str, Any] = {"key": self.storage_key, "secret": self.storage_secret}
        if self.storage_endpoint_url:
            opts["client_kwargs"] = {"endpoint_url": self.storage_endpoint_url}
        return opts

    def object_url(self, bucket: str, key: str) -> str:
        """s3://bucket/key or gs://bucket/key; a local path when storage_protocol is "file" (tests)."""
        if self.storage_protocol == "file":  # tests/offline: buckets are local folders, keys are paths
            return str(Path(bucket, *key.split("/")))
        return f"{self.storage_protocol}://{bucket}/{key}"

    @property
    def jwks_url(self) -> str:
        return self.oidc_jwks_url or f"{self.oidc_issuer.rstrip('/')}/protocol/openid-connect/certs"


@lru_cache
def get_settings() -> Settings:
    return Settings()
