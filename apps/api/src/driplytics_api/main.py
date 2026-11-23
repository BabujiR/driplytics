"""Driplytics API entry point: `uvicorn driplytics_api.main:app`."""

import logging
from typing import Any

from fastapi import FastAPI, Response, status
from fastapi.routing import APIRoute
from starlette.concurrency import run_in_threadpool

from . import __version__
from .health import CHECKS
from .responses import LiveOut, ReadinessOut, VersionOut
from .routes import audit, imports, me, sites
from .settings import get_settings

settings = get_settings()
logging.basicConfig(level=settings.log_level, format="%(asctime)s %(levelname)s %(name)s %(message)s")


def operation_id(route: APIRoute) -> str:
    """Stable, readable operationIds for the generated client: the route function's name."""
    return route.name


app = FastAPI(
    title="Driplytics API",
    generate_unique_id_function=operation_id,
    version=__version__,
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)
app.include_router(me.router)
app.include_router(sites.router)
app.include_router(imports.router)
app.include_router(audit.router)


@app.get("/health/live", tags=["health"], response_model=LiveOut)
def live() -> dict[str, str]:
    """Liveness: the process is up. No dependency checks."""
    return {"status": "ok"}


@app.get(
    "/health/ready",
    tags=["health"],
    response_model=ReadinessOut,
    responses={503: {"model": ReadinessOut, "description": "A dependency is down"}},
)
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


@app.get("/api/v1/version", tags=["meta"], response_model=VersionOut)
def version() -> dict[str, str]:
    return {"service": "driplytics-api", "version": __version__, "env": settings.env}
