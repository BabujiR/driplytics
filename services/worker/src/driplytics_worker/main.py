"""Arq worker entry point: `arq driplytics_worker.main.WorkerSettings`.

Jobs: `ping` (queue health) and `import_file` (P0-12, historian import).
"""

import asyncio
import logging
from typing import Any, ClassVar
from uuid import UUID

from arq.connections import RedisSettings

from . import __version__
from .import_job import run_import
from .settings import get_config

config = get_config()
logging.basicConfig(level=config.log_level, format="%(asctime)s %(levelname)s %(name)s %(message)s")
log = logging.getLogger("driplytics.worker")


async def ping(ctx: dict[str, Any], message: str = "ping") -> str:
    """Health job: returns 'pong' (or echoes the message)."""
    return "pong" if message == "ping" else message


async def import_file(ctx: dict[str, Any], import_id: str, tenant_id: str) -> dict[str, Any]:
    """P0-12: run one historian import (CPU-bound work runs in a thread, keeping the event loop free)."""
    return await asyncio.to_thread(run_import, config, UUID(import_id), UUID(tenant_id))


def engine_version() -> str:
    """Prove the workspace wiring: the worker can import the engine package."""
    import driplytics_engine  # imported lazily so the worker starts fast

    return getattr(driplytics_engine, "__version__", "installed")


async def startup(ctx: dict[str, Any]) -> None:
    log.info("driplytics-worker %s starting (env=%s, engine=%s)", __version__, config.env, engine_version())


async def shutdown(ctx: dict[str, Any]) -> None:
    log.info("driplytics-worker stopping")


class WorkerSettings:
    functions: ClassVar[list[Any]] = [ping, import_file]
    on_startup = startup
    on_shutdown = shutdown
    redis_settings = RedisSettings.from_dsn(config.redis_url)
    max_jobs = config.max_jobs
    job_timeout = config.job_timeout_s
    health_check_interval = 30  # lets `arq --check` (the container health check) work
