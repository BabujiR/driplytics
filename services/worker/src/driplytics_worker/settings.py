from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class WorkerConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="DRIPLYTICS_", env_file=".env", extra="ignore")

    env: str = "local"
    log_level: str = "INFO"
    redis_url: str = "redis://localhost:6379/0"
    max_jobs: int = 4
    job_timeout_s: int = 3600


@lru_cache
def get_config() -> WorkerConfig:
    return WorkerConfig()
