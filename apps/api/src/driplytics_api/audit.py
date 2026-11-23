"""Audit log (P0-09). Append-only: the runtime role can INSERT and SELECT audit_event, never change it.

Every mutating endpoint calls `record(...)` inside the SAME transaction as its change, so an audit
entry exists if and only if the change was committed.
"""

from typing import Any
from uuid import UUID

from psycopg.types.json import Jsonb

from driplytics_api.db.connection import Conn


def record(
    conn: Conn,
    *,
    tenant_id: UUID,
    user_id: UUID | None,
    action: str,
    entity_type: str,
    entity_id: UUID | str | None,
    before: dict[str, Any] | None = None,
    after: dict[str, Any] | None = None,
) -> None:
    """`action` is '<entity>.<verb>', e.g. 'site.create', 'tag_mapping.import', 'import.queue'."""
    conn.execute(
        "INSERT INTO audit_event (tenant_id, user_id, action, entity_type, entity_id, before, after) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s)",
        (
            tenant_id,
            user_id,
            action,
            entity_type,
            str(entity_id) if entity_id is not None else None,
            Jsonb(_jsonable(before)) if before is not None else None,
            Jsonb(_jsonable(after)) if after is not None else None,
        ),
    )


def _jsonable(value: Any) -> Any:
    """UUIDs and datetimes from DB rows -> strings, so they can be stored as JSON."""
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, list | tuple):
        return [_jsonable(v) for v in value]
    if value is None or isinstance(value, bool | int | float | str):
        return value
    return str(value)
