"""Connections for request handling.

Every query against tenant data runs inside `request_tx(...)`, which sets the row-level
security context for THAT transaction only (`set_config(..., is_local => true)`). The context
ends at commit or rollback, so it can never leak into the next request on a reused connection.
"""

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any
from uuid import UUID

import psycopg
from psycopg.rows import dict_row

Conn = psycopg.Connection[dict[str, Any]]


@contextmanager
def request_tx(
    database_url: str, *, user_id: UUID | None = None, tenant_id: UUID | None = None
) -> Iterator[Conn]:
    """One transaction as the runtime role, with app.user_id / app.tenant_id set."""
    with psycopg.connect(database_url, row_factory=dict_row) as conn, conn.transaction():
        conn.execute(
            "SELECT set_config('app.user_id', %s, true), set_config('app.tenant_id', %s, true)",
            (str(user_id) if user_id else "", str(tenant_id) if tenant_id else ""),
        )
        yield conn
