"""Enqueue background jobs (Arq on Redis, ADR 0006). Swappable in tests via dependency override."""

from typing import Annotated, Protocol
from uuid import UUID

from fastapi import Depends

from .settings import Settings, get_settings


class JobQueue(Protocol):
    async def enqueue_import(self, import_id: UUID, tenant_id: UUID) -> None: ...


class ArqQueue:
    def __init__(self, redis_url: str) -> None:
        self.redis_url = redis_url

    async def enqueue_import(self, import_id: UUID, tenant_id: UUID) -> None:
        from arq import create_pool
        from arq.connections import RedisSettings

        pool = await create_pool(RedisSettings.from_dsn(self.redis_url))
        try:
            # _job_id makes enqueueing idempotent: the same import is never queued twice.
            await pool.enqueue_job(
                "import_file", str(import_id), str(tenant_id), _job_id=f"import:{import_id}"
            )
        finally:
            await pool.aclose()


def get_queue(settings: Annotated[Settings, Depends(get_settings)]) -> JobQueue:
    return ArqQueue(settings.redis_url)
