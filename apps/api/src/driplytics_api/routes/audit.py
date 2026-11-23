"""Read the audit log of the current organization (admins and owners)."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query

from driplytics_api.auth.deps import TenantContext, require_role
from driplytics_api.auth.roles import Role
from driplytics_api.db.connection import request_tx
from driplytics_api.responses import COMMON_ERRORS, AuditEventOut
from driplytics_api.settings import Settings, get_settings

router = APIRouter(prefix="/api/v1", tags=["audit"], responses=COMMON_ERRORS)


@router.get("/audit", response_model=list[AuditEventOut])
def list_audit_events(
    ctx: Annotated[TenantContext, Depends(require_role(Role.ADMIN))],
    settings: Annotated[Settings, Depends(get_settings)],
    entity_type: str | None = None,
    entity_id: str | None = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> list[dict[str, Any]]:
    """Newest first. Filter by entity, e.g. ?entity_type=site&entity_id=<uuid>."""
    with request_tx(settings.database_url, user_id=ctx.principal.user_id, tenant_id=ctx.tenant_id) as conn:
        rows = conn.execute(
            "SELECT e.id, e.at, e.action, e.entity_type, e.entity_id, e.before, e.after, "
            "u.email AS user_email FROM audit_event e LEFT JOIN app_user u ON u.id = e.user_id "
            "WHERE (%(t)s::text IS NULL OR e.entity_type = %(t)s) AND (%(i)s::text IS NULL OR e.entity_id = %(i)s) "
            "ORDER BY e.at DESC, e.id LIMIT %(n)s",
            {"t": entity_type, "i": entity_id, "n": limit},
        ).fetchall()
    return rows
