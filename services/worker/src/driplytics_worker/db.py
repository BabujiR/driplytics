"""Worker database access: the same per-transaction tenant context as the API (ADR 0003, 0018)."""

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any
from uuid import UUID

import psycopg
from psycopg.rows import dict_row

Conn = psycopg.Connection[dict[str, Any]]


@contextmanager
def tenant_tx(database_url: str, tenant_id: UUID) -> Iterator[Conn]:
    with psycopg.connect(database_url, row_factory=dict_row) as conn, conn.transaction():
        conn.execute("SELECT set_config('app.tenant_id', %s, true)", (str(tenant_id),))
        yield conn
