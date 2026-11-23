"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}
"""

from alembic import op

revision = ${repr(up_revision)}
down_revision = ${repr(down_revision)}
branch_labels = ${repr(branch_labels)}
depends_on = ${repr(depends_on)}


def upgrade() -> None:
    # Every new tenant-owned table needs: tenant_id NOT NULL, composite FKs to its parent,
    # ENABLE + FORCE ROW LEVEL SECURITY and a tenant_isolation policy (ADR 0003).
    # tests/db/test_schema_lint.py fails the build otherwise.
    ...


def downgrade() -> None:
    ...
