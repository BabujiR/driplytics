"""Shared helpers for API tests: signed test tokens and an app with test overrides."""

import time
from typing import Any
from uuid import UUID

import jwt
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import FastAPI

from driplytics_api.auth.deps import get_verifier
from driplytics_api.auth.oidc import TokenVerifier
from driplytics_api.queue import get_queue
from driplytics_api.routes import audit, imports, me, sites
from driplytics_api.settings import Settings, get_settings

ISSUER = "http://localhost:8080/realms/driplytics"
KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)


def auth(sub: str, email: str, tenant: UUID | None = None) -> dict[str, str]:
    now = int(time.time())
    claims = {
        "iss": ISSUER,
        "sub": sub,
        "azp": "driplytics-web",
        "iat": now,
        "exp": now + 300,
        "email": email,
        "email_verified": True,
    }
    headers = {"Authorization": f"Bearer {jwt.encode(claims, KEY, algorithm='RS256')}"}
    if tenant is not None:
        headers["X-Tenant-Id"] = str(tenant)
    return headers


class FakeQueue:
    def __init__(self) -> None:
        self.jobs: list[tuple[UUID, UUID]] = []

    async def enqueue_import(self, import_id: UUID, tenant_id: UUID) -> None:
        self.jobs.append((import_id, tenant_id))


def make_app(settings: Settings, queue: FakeQueue) -> FastAPI:
    app = FastAPI()
    for r in (me.router, sites.router, imports.router, audit.router):
        app.include_router(r)
    app.dependency_overrides[get_settings] = lambda: settings
    app.dependency_overrides[get_queue] = lambda: queue
    app.dependency_overrides[get_verifier] = lambda: TokenVerifier(
        issuer=ISSUER, key_resolver=lambda _t: KEY.public_key(), client_ids=["driplytics-web"]
    )
    return app


def any_(d: dict[str, Any], *keys: str) -> Any:
    for k in keys:
        d = d[k]
    return d
