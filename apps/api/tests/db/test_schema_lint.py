"""Schema guard rails (P0-07): every new table must follow the tenancy rules (ADR 0003).

If this fails after you add a migration: give the table tenant_id NOT NULL, composite FKs to its
parent, ENABLE + FORCE ROW LEVEL SECURITY and a tenant_isolation policy, or add it to
GLOBAL_TABLES with a comment explaining why it is not tenant data.
"""

import psycopg
import pytest

pytestmark = pytest.mark.db

GLOBAL_TABLES = {
    "app_user",  # people can belong to several tenants
    "alembic_version",  # migration bookkeeping, no runtime grants
}

TABLES = """
SELECT c.relname, c.relrowsecurity, c.relforcerowsecurity,
       (SELECT count(*) FROM pg_policy p WHERE p.polrelid = c.oid) AS policies,
       EXISTS (SELECT 1 FROM information_schema.columns col
               WHERE col.table_schema = 'public' AND col.table_name = c.relname
                 AND col.column_name = 'tenant_id') AS has_tenant_id
FROM pg_class c WHERE c.relnamespace = 'public'::regnamespace AND c.relkind IN ('r', 'p')
"""


def test_every_non_global_table_has_forced_rls_and_a_policy(test_db) -> None:
    with psycopg.connect(test_db.admin_url) as conn:
        rows = conn.execute(TABLES).fetchall()
    problems = []
    for name, rls, forced, policies, has_tenant in rows:
        if name in GLOBAL_TABLES:
            continue
        if not (rls and forced and policies):
            problems.append(f"{name}: rls={rls} forced={forced} policies={policies}")
        if not has_tenant and name not in {"tenant"}:
            problems.append(f"{name}: no tenant_id column")
    assert not problems, "tables breaking ADR 0003:\n  " + "\n  ".join(problems)


def test_global_tables_are_still_global(test_db) -> None:
    with psycopg.connect(test_db.admin_url) as conn:
        names = {r[0] for r in conn.execute(TABLES).fetchall()}
    assert {"app_user"} <= names


def test_runtime_role_privileges(test_db) -> None:
    with psycopg.connect(test_db.admin_url) as conn:

        def can(table: str, priv: str) -> bool:
            return bool(
                conn.execute(
                    "SELECT has_table_privilege('driplytics_app', %s, %s)", (table, priv)
                ).fetchone()[0]
            )

        assert (
            can("audit_event", "INSERT")
            and not can("audit_event", "UPDATE")
            and not can("audit_event", "DELETE")
        )
        assert not can("tenant", "INSERT") and not can("tenant", "DELETE")
        assert not can("alembic_version", "SELECT")
