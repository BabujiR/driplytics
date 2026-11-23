"""Who am I, and which organizations can I switch to?"""

from typing import Annotated, Any

from fastapi import APIRouter, Depends

from driplytics_api.auth.deps import Principal, TenantContext, current_principal, require_role
from driplytics_api.auth.roles import Role
from driplytics_api.db.connection import request_tx
from driplytics_api.settings import Settings, get_settings

router = APIRouter(prefix="/api/v1", tags=["identity"])


@router.get("/me")
def me(
    principal: Annotated[Principal, Depends(current_principal)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> dict[str, Any]:
    with request_tx(settings.database_url, user_id=principal.user_id) as conn:
        user = conn.execute(
            "SELECT id, email, display_name, last_login_at FROM app_user WHERE id = %s", (principal.user_id,)
        ).fetchone()
        memberships = conn.execute(
            "SELECT t.id AS tenant_id, t.name, t.slug, t.plan, m.role "
            "FROM membership m JOIN tenant t ON t.id = m.tenant_id ORDER BY t.name"
        ).fetchall()
    return {"user": user, "memberships": memberships}


@router.get("/tenants/current")
def current_tenant_info(
    ctx: Annotated[TenantContext, Depends(require_role(Role.VIEWER))],
    settings: Annotated[Settings, Depends(get_settings)],
) -> dict[str, Any]:
    """The selected organization, read through row-level security as the caller's tenant."""
    with request_tx(settings.database_url, user_id=ctx.principal.user_id, tenant_id=ctx.tenant_id) as conn:
        tenant = conn.execute(
            "SELECT id, name, slug, plan, created_at FROM tenant WHERE id = %s", (ctx.tenant_id,)
        ).fetchone()
        sites = conn.execute("SELECT id, name, timezone, display_units FROM site ORDER BY name").fetchall()
    return {"tenant": tenant, "role": ctx.role.value, "sites": sites}
