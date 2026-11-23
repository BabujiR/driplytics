"""Initial schema: tenancy, users, plant model, imports, jobs, audit, row-level security.

Revision ID: 0001
Revises:
Create Date: 2026-11-23

The DDL lives in 0001_initial_schema.up.sql / .down.sql so it can be read, reviewed and
tested with plain psql.
"""

from pathlib import Path

from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

_HERE = Path(__file__).parent


def _run_sql_file(name: str) -> None:
    sql_text = (_HERE / name).read_text(encoding="utf-8")
    # Raw psycopg cursor: multi-statement SQL (DO $$ blocks) and no bind-parameter parsing.
    dbapi_conn = op.get_bind().connection.dbapi_connection
    with dbapi_conn.cursor() as cur:
        cur.execute(sql_text)


def upgrade() -> None:
    _run_sql_file("0001_initial_schema.up.sql")


def downgrade() -> None:
    _run_sql_file("0001_initial_schema.down.sql")
