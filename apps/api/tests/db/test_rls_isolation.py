"""Cross-tenant isolation (P0-07, ADR 0003). Runs as driplytics_app, exactly like the API."""

import psycopg
import pytest
from psycopg import errors, sql

from driplytics_api.db.connection import request_tx

from .conftest import ALICE, TENANT_A, TENANT_B, TENANT_TABLES, tx

pytestmark = pytest.mark.db


def count(conn, table: str, where: str = "", params: tuple = ()) -> int:  # type: ignore[no-untyped-def]
    q = sql.SQL("SELECT count(*) AS n FROM {}").format(sql.Identifier(table))
    if where:
        q = q + sql.SQL(" WHERE ") + sql.SQL(where)  # type: ignore[arg-type]
    row = conn.execute(q, params).fetchone()
    return int(row["n"] if isinstance(row, dict) else row[0])


def test_runtime_role_cannot_bypass_rls(seeded) -> None:
    with request_tx(seeded.app_url) as conn:
        row = conn.execute(
            "SELECT rolsuper, rolbypassrls FROM pg_roles WHERE rolname = current_user"
        ).fetchone()
    assert row == {"rolsuper": False, "rolbypassrls": False}


@pytest.mark.parametrize("table", [*TENANT_TABLES, "membership", "tenant"])
def test_fail_closed_without_tenant(seeded, table: str) -> None:
    with tx(seeded.app_url) as conn:
        assert count(conn, table) == 0


@pytest.mark.parametrize("table", TENANT_TABLES)
def test_tenant_sees_only_its_own_rows(seeded, table: str) -> None:
    with tx(seeded.app_url, tenant_id=TENANT_A) as conn:
        assert count(conn, table) == 1
        assert count(conn, table, "tenant_id <> %s", (TENANT_A,)) == 0


@pytest.mark.parametrize("table", TENANT_TABLES[:-1])  # audit_event: UPDATE/DELETE not even granted
def test_update_and_delete_of_other_tenant_touch_nothing(seeded, table: str) -> None:
    with tx(seeded.app_url, tenant_id=TENANT_A) as conn:
        upd = conn.execute(
            sql.SQL("UPDATE {} SET tenant_id = tenant_id WHERE tenant_id = %s").format(sql.Identifier(table)),
            (TENANT_B,),
        )
        assert upd.rowcount == 0
        dele = conn.execute(
            sql.SQL("DELETE FROM {} WHERE tenant_id = %s").format(sql.Identifier(table)), (TENANT_B,)
        )
        assert dele.rowcount == 0
    with psycopg.connect(seeded.admin_url) as admin:  # B's data is really still there
        assert count(admin, table, "tenant_id = %s", (TENANT_B,)) == 1


def test_insert_for_other_tenant_is_rejected(seeded) -> None:
    with tx(seeded.app_url, tenant_id=TENANT_A) as conn:
        with pytest.raises(errors.InsufficientPrivilege), conn.transaction():
            conn.execute("INSERT INTO site (tenant_id, name) VALUES (%s, 'smuggled')", (TENANT_B,))
        with pytest.raises(errors.InsufficientPrivilege), conn.transaction():
            conn.execute("UPDATE site SET tenant_id = %s WHERE tenant_id = %s", (TENANT_B, TENANT_A))


def test_cannot_attach_to_other_tenants_parent_even_with_its_id(seeded) -> None:
    with psycopg.connect(seeded.admin_url) as admin:
        b_site = admin.execute("SELECT id FROM site WHERE tenant_id = %s", (TENANT_B,)).fetchone()[0]
    with (
        tx(seeded.app_url, tenant_id=TENANT_A) as conn,
        pytest.raises(errors.ForeignKeyViolation),
        conn.transaction(),
    ):
        conn.execute("INSERT INTO area (tenant_id, site_id, name) VALUES (%s, %s, 'x')", (TENANT_A, b_site))


def test_audit_log_is_append_only(seeded) -> None:
    with tx(seeded.app_url, tenant_id=TENANT_A) as conn:
        conn.execute("INSERT INTO audit_event (tenant_id, action) VALUES (%s, 'test.ok')", (TENANT_A,))
        for stmt in ("UPDATE audit_event SET action = 'tampered'", "DELETE FROM audit_event"):
            with pytest.raises(errors.InsufficientPrivilege), conn.transaction():
                conn.execute(stmt)


def test_database_enforces_import_accounting(seeded) -> None:
    with tx(seeded.app_url, tenant_id=TENANT_A) as conn:
        site = conn.execute("SELECT id FROM site").fetchone()["id"]
        imp = conn.execute(
            "INSERT INTO data_import (tenant_id, site_id, object_key) VALUES (%s, %s, 'raw/y.csv') "
            "RETURNING id",
            (TENANT_A, site),
        ).fetchone()["id"]
        report = (
            "INSERT INTO import_report (import_id, tenant_id, total_values, accepted, rejected, duplicates, "
            "report, scoring_allowed) VALUES (%s, %s, 10, %s, 1, 1, '{}', true)"
        )
        with pytest.raises(errors.CheckViolation), conn.transaction():
            conn.execute(report, (imp, TENANT_A, 5))  # 5 + 1 + 1 != 10
        conn.execute(report, (imp, TENANT_A, 8))  # 8 + 1 + 1 == 10


def test_runtime_role_cannot_create_tenants(seeded) -> None:
    with (
        tx(seeded.app_url, tenant_id=TENANT_A) as conn,
        pytest.raises(errors.InsufficientPrivilege),
        conn.transaction(),
    ):
        conn.execute("INSERT INTO tenant (name, slug) VALUES ('Evil', 'evil')")


def test_user_context_shows_own_memberships_and_tenants_only(seeded) -> None:
    with tx(seeded.app_url, user_id=ALICE) as conn:
        assert [r["tenant_id"] for r in conn.execute("SELECT tenant_id FROM membership")] == [TENANT_A]
        assert [r["slug"] for r in conn.execute("SELECT slug FROM tenant")] == ["tenant-a"]
        assert count(conn, "site") == 0  # knowing your user id never exposes tenant data


def test_context_is_transaction_local(seeded) -> None:
    with psycopg.connect(seeded.app_url) as conn:
        with conn.transaction():
            conn.execute("SELECT set_config('app.tenant_id', %s, true)", (str(TENANT_A),))
            assert conn.execute("SELECT count(*) FROM site").fetchone()[0] == 1
        # same connection, next transaction: context is gone (no leak between pooled requests)
        assert conn.execute("SELECT count(*) FROM site").fetchone()[0] == 0
