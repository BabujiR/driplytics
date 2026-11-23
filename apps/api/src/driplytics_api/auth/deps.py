"""FastAPI dependencies: who is calling, and in which tenant, with which role."""

from collections.abc import Callable
from dataclasses import dataclass
from functools import lru_cache
from typing import Annotated
from uuid import UUID

from fastapi import Depends, Header, HTTPException, status

from driplytics_api.db.connection import request_tx
from driplytics_api.settings import Settings, get_settings

from .oidc import Claims, TokenError, TokenVerifier, jwks_key_resolver
from .provisioning import ProvisioningError, provision_user
from .roles import Role, has_at_least

_UNAUTHORIZED = {"WWW-Authenticate": "Bearer"}


@lru_cache
def _build_verifier(
    issuer: str, jwks_url: str, client_ids: tuple[str, ...], audience: str | None, leeway_s: int
) -> TokenVerifier:
    return TokenVerifier(
        issuer=issuer,
        key_resolver=jwks_key_resolver(jwks_url),
        client_ids=list(client_ids),
        audience=audience,
        leeway_s=leeway_s,
    )


def get_verifier(settings: Annotated[Settings, Depends(get_settings)]) -> TokenVerifier:
    return _build_verifier(
        settings.oidc_issuer,
        settings.jwks_url,
        tuple(settings.oidc_client_ids),
        settings.oidc_audience,
        settings.oidc_leeway_s,
    )


@dataclass(frozen=True)
class Principal:
    user_id: UUID
    claims: Claims


@dataclass(frozen=True)
class TenantContext:
    principal: Principal
    tenant_id: UUID
    role: Role


def current_principal(
    settings: Annotated[Settings, Depends(get_settings)],
    verifier: Annotated[TokenVerifier, Depends(get_verifier)],
    authorization: Annotated[str | None, Header()] = None,
) -> Principal:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "sign-in required", headers=_UNAUTHORIZED)
    try:
        claims = verifier.verify(authorization.split(" ", 1)[1].strip())
    except TokenError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, str(exc), headers=_UNAUTHORIZED) from exc
    try:
        with request_tx(settings.database_url) as conn:
            user_id = provision_user(conn, claims)
    except ProvisioningError as exc:
        raise HTTPException(status.HTTP_403_FORBIDDEN, str(exc)) from exc
    return Principal(user_id=user_id, claims=claims)


def current_tenant(
    settings: Annotated[Settings, Depends(get_settings)],
    principal: Annotated[Principal, Depends(current_principal)],
    x_tenant_id: Annotated[UUID | None, Header()] = None,
) -> TenantContext:
    """The tenant comes from the X-Tenant-Id header and must be one of the caller's memberships."""
    if x_tenant_id is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "X-Tenant-Id header required")
    with request_tx(settings.database_url, user_id=principal.user_id) as conn:
        row = conn.execute(
            "SELECT role FROM membership WHERE tenant_id = %s AND user_id = %s",
            (x_tenant_id, principal.user_id),
        ).fetchone()
    if not row:
        # Same answer whether the tenant exists or not: don't reveal other tenants.
        raise HTTPException(status.HTTP_403_FORBIDDEN, "you are not a member of this organization")
    return TenantContext(principal=principal, tenant_id=x_tenant_id, role=Role(row["role"]))


def require_role(minimum: Role) -> Callable[[TenantContext], TenantContext]:
    """Dependency factory: `ctx: TenantContext = Depends(require_role(Role.ENGINEER))`."""

    def check(ctx: Annotated[TenantContext, Depends(current_tenant)]) -> TenantContext:
        if not has_at_least(ctx.role, minimum):
            raise HTTPException(status.HTTP_403_FORBIDDEN, f"requires the {minimum.value} role or higher")
        return ctx

    return check
