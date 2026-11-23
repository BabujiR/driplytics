"""Sign-in, provisioning, tenant selection and role checks through the real API routes (P0-08).

Tokens are signed with a test RSA key and the verifier is swapped in through FastAPI's
dependency overrides, so no identity provider is needed. The database is the real test DB.
"""

import time
import uuid
from collections.abc import Iterator
from typing import Annotated, Any

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from driplytics_api.auth.deps import TenantContext, get_verifier, require_role
from driplytics_api.auth.oidc import TokenVerifier
from driplytics_api.auth.roles import Role
from driplytics_api.routes import me
from driplytics_api.settings import Settings, get_settings

from .conftest import TENANT_A, TENANT_B

pytestmark = pytest.mark.db

ISSUER = "http://localhost:8080/realms/driplytics"
KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)


def token(sub: str, email: str, verified: bool = True, **extra: Any) -> dict[str, str]:
    now = int(time.time())
    claims = {
        "iss": ISSUER,
        "sub": sub,
        "azp": "driplytics-web",
        "iat": now,
        "exp": now + 300,
        "email": email,
        "email_verified": verified,
        **extra,
    }
    return {"Authorization": f"Bearer {jwt.encode(claims, KEY, algorithm='RS256')}"}


@pytest.fixture
def client(seeded) -> Iterator[TestClient]:
    app = FastAPI()
    app.include_router(me.router)

    @app.get("/test/engineer-only")
    def engineer_only(ctx: Annotated[TenantContext, Depends(require_role(Role.ENGINEER))]) -> dict[str, str]:
        return {"role": ctx.role.value}

    app.dependency_overrides[get_settings] = lambda: Settings(database_url=seeded.app_url)
    app.dependency_overrides[get_verifier] = lambda: TokenVerifier(
        issuer=ISSUER, key_resolver=lambda _t: KEY.public_key(), client_ids=["driplytics-web"]
    )
    with TestClient(app) as c:
        yield c


# ---------------------------------------------------------------- authentication
def test_no_token_is_401(client: TestClient) -> None:
    r = client.get("/api/v1/me")
    assert r.status_code == 401 and r.headers["www-authenticate"] == "Bearer"


def test_bad_token_is_401(client: TestClient) -> None:
    assert client.get("/api/v1/me", headers={"Authorization": "Bearer nope"}).status_code == 401


def test_me_for_known_user(client: TestClient) -> None:
    r = client.get("/api/v1/me", headers=token("kc-alice", "alice@a.test"))
    assert r.status_code == 200
    body = r.json()
    assert body["user"]["email"] == "alice@a.test"
    assert [(m["slug"], m["role"]) for m in body["memberships"]] == [("tenant-a", "owner")]


# ---------------------------------------------------------------- provisioning
def test_new_person_gets_an_account_with_no_access(client: TestClient) -> None:
    email = f"carol-{uuid.uuid4().hex[:6]}@new.test"
    r = client.get("/api/v1/me", headers=token(f"kc-{email}", email))
    assert r.status_code == 200 and r.json()["memberships"] == []


def test_unverified_email_is_refused(client: TestClient) -> None:
    r = client.get("/api/v1/me", headers=token("kc-unverified", "dave@new.test", verified=False))
    assert r.status_code == 403 and "not verified" in r.json()["detail"]


def test_someone_elses_email_with_a_different_subject_is_refused(client: TestClient) -> None:
    r = client.get("/api/v1/me", headers=token("kc-attacker", "alice@a.test"))
    assert r.status_code == 403 and "already linked" in r.json()["detail"]


# ---------------------------------------------------------------- tenant selection and roles
def test_current_tenant_for_member(client: TestClient) -> None:
    r = client.get(
        "/api/v1/tenants/current", headers={**token("kc-alice", "alice@a.test"), "X-Tenant-Id": str(TENANT_A)}
    )
    assert r.status_code == 200
    assert r.json()["tenant"]["slug"] == "tenant-a" and r.json()["role"] == "owner"
    assert len(r.json()["sites"]) == 1


def test_other_tenant_is_403_and_does_not_reveal_existence(client: TestClient) -> None:
    alice = token("kc-alice", "alice@a.test")
    real = client.get("/api/v1/tenants/current", headers={**alice, "X-Tenant-Id": str(TENANT_B)})
    fake = client.get("/api/v1/tenants/current", headers={**alice, "X-Tenant-Id": str(uuid.uuid4())})
    assert real.status_code == fake.status_code == 403
    assert real.json() == fake.json()


def test_missing_tenant_header_is_400(client: TestClient) -> None:
    assert client.get("/api/v1/tenants/current", headers=token("kc-alice", "alice@a.test")).status_code == 400


def test_role_check(client: TestClient) -> None:
    alice = {**token("kc-alice", "alice@a.test"), "X-Tenant-Id": str(TENANT_A)}  # owner
    bob = {**token("kc-bob", "bob@b.test"), "X-Tenant-Id": str(TENANT_B)}  # viewer
    assert client.get("/test/engineer-only", headers=alice).json() == {"role": "owner"}
    r = client.get("/test/engineer-only", headers=bob)
    assert r.status_code == 403 and "engineer" in r.json()["detail"]
    assert client.get("/api/v1/tenants/current", headers=bob).json()["role"] == "viewer"
