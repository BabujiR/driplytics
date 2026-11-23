"""Driplytics API entry point: `uvicorn driplytics_api.main:app`."""

import logging
from typing import Any

from fastapi import FastAPI, Response, status
from starlette.concurrency import run_in_threadpool

from . import __version__
from .health import CHECKS
from .routes import me
from .settings import get_settings

settings = get_settings()
logging.basicConfig(level=settings.log_level, format="%(asctime)s %(levelname)s %(name)s %(message)s")

app = FastAPI(
    title="Driplytics API",
    version=__version__,
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)
app.include_router(me.router)


@app.get("/health/live", tags=["health"])
def live() -> dict[str, str]:
    """Liveness: the process is up. No dependency checks."""
    return {"status": "ok"}


@app.get("/health/ready", tags=["health"])
async def ready(response: Response) -> dict[str, Any]:
    """Readiness: Postgres, Redis and object storage are reachable. 503 if any check fails."""
    results = {name: await run_in_threadpool(check, settings) for name, check in CHECKS.items()}
    all_ok = all(r.ok for r in results.values())
    if not all_ok:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return {
        "status": "ok" if all_ok else "degraded",
        "checks": {name: {"ok": r.ok, "detail": r.detail} for name, r in results.items()},
    }


@app.get("/api/v1/version", tags=["meta"])
def version() -> dict[str, str]:
    return {"service": "driplytics-api", "version": __version__, "env": settings.env}
