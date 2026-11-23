"""Arq worker entry point: `arq driplytics_worker.main.WorkerSettings`.

Phase 0 registers a `ping` job to prove the queue round-trip. The import job (P0-12) is added next.
"""

import logging
from typing import Any, ClassVar

from arq.connections import RedisSettings

from . import __version__
from .settings import get_config

config = get_config()
logging.basicConfig(level=config.log_level, format="%(asctime)s %(levelname)s %(name)s %(message)s")
log = logging.getLogger("driplytics.worker")


async def ping(ctx: dict[str, Any], message: str = "ping") -> str:
    """Health job: returns 'pong' (or echoes the message)."""
    return "pong" if message == "ping" else message


def engine_version() -> str:
    """Prove the workspace wiring: the worker can import the engine package."""
    import driplytics_engine  # imported lazily so the worker starts fast

    return getattr(driplytics_engine, "__version__", "installed")


async def startup(ctx: dict[str, Any]) -> None:
    log.info("driplytics-worker %s starting (env=%s, engine=%s)", __version__, config.env, engine_version())


async def shutdown(ctx: dict[str, Any]) -> None:
    log.info("driplytics-worker stopping")


class WorkerSettings:
    functions: ClassVar[list[Any]] = [ping]
    on_startup = startup
    on_shutdown = shutdown
    redis_settings = RedisSettings.from_dsn(config.redis_url)
    max_jobs = config.max_jobs
    job_timeout = config.job_timeout_s
    health_check_interval = 30  # lets `arq --check` (the container health check) work
