"""Database test fixtures (P0-07).

These tests need PostgreSQL: start it with `docker compose up -d postgres`. They create a fresh,
throwaway database per test session, migrate it, and drop it afterwards. Without Postgres they
are skipped, so the plain unit-test run still works anywhere.

    DRIPLYTICS_TEST_ADMIN_URL  superuser URL (default: the local compose Postgres, db 'postgres')
"""

import os
import shutil
import tempfile
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit, urlunsplit

import psycopg
import pytest
from psycopg import sql
from psycopg.rows import dict_row

from driplytics_api.db import migrate
from driplytics_api.settings import Settings

ADMIN_URL = os.environ.get(
    "DRIPLYTICS_TEST_ADMIN_URL", "postgresql://driplytics:driplytics-dev@localhost:5432/postgres"
)
TENANT_A = uuid.UUID("aaaaaaaa-0000-4000-8000-000000000001")
TENANT_B = uuid.UUID("bbbbbbbb-0000-4000-8000-000000000002")
TENANT_TABLES = [
    "site",
    "area",
    "asset",
    "tag",
    "tag_mapping",
    "export_profile",
    "data_import",
    "import_report",
    "job",
    "audit_event",
]


def _with_db(url: str, db: str) -> str:
    p = urlsplit(url)
    return urlunsplit((p.scheme, p.netloc, f"/{db}", p.query, p.fragment))


def _with_credentials(url: str, user: str, password: str) -> str:
    p = urlsplit(url)
    host = p.hostname or "localhost"
    netloc = f"{user}:{password}@{host}" + (f":{p.port}" if p.port else "")
    return urlunsplit((p.scheme, netloc, p.path, p.query, p.fragment))


@dataclass(frozen=True)
class TestDB:
    admin_url: str  # superuser, bypasses RLS: used only to seed
    app_url: str  # driplytics_app: what the API uses; everything under test goes through this


@pytest.fixture(scope="session")
def test_db() -> Iterator[TestDB]:
    try:
        psycopg.connect(ADMIN_URL, connect_timeout=2).close()
    except psycopg.OperationalError:
        if os.environ.get("DRIPLYTICS_REQUIRE_DB"):  # CI: a missing database is a failure, never a skip
            pytest.fail(f"PostgreSQL required but not reachable at {ADMIN_URL.split('@')[-1]}")
        pytest.skip(
            f"PostgreSQL not reachable at {ADMIN_URL.split('@')[-1]} (run: docker compose up -d postgres)"
        )

    name = f"driplytics_test_{uuid.uuid4().hex[:10]}"
    with psycopg.connect(ADMIN_URL, autocommit=True) as conn:
        conn.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(name)))
    admin_url = _with_db(ADMIN_URL, name)
    # Reuse the configured runtime password: the role is cluster-wide and shared with the dev stack.
    app = urlsplit(Settings().database_url)
    app_url = _with_credentials(admin_url, app.username or "driplytics_app", app.password or "")
    try:
        migrate.upgrade(admin_url, app_url)
        yield TestDB(admin_url=admin_url, app_url=app_url)
    finally:
        with psycopg.connect(ADMIN_URL, autocommit=True) as conn:
            conn.execute(sql.SQL("DROP DATABASE IF EXISTS {} WITH (FORCE)").format(sql.Identifier(name)))


ALICE = uuid.UUID("aaaaaaaa-1111-4000-8000-000000000001")
BOB = uuid.UUID("bbbbbbbb-1111-4000-8000-000000000002")

# psycopg runs ONE statement per execute() when parameters are passed, so these are lists.
SEED = [
    "INSERT INTO tenant (id, name, slug) VALUES (%(a)s, 'Tenant A', 'tenant-a'), (%(b)s, 'Tenant B', 'tenant-b')",
    "INSERT INTO app_user (id, email, idp_subject) VALUES (%(alice)s, 'alice@a.test', 'kc-alice'), "
    "(%(bob)s, 'bob@b.test', 'kc-bob')",
    "INSERT INTO membership (tenant_id, user_id, role) VALUES (%(a)s, %(alice)s, 'owner'), (%(b)s, %(bob)s, 'viewer')",
]
SEED_TENANT = [
    """WITH s AS (INSERT INTO site (tenant_id, name) VALUES (%(t)s, 'Main plant') RETURNING id),
     ar AS (INSERT INTO area (tenant_id, site_id, name) SELECT %(t)s, id, 'Filters' FROM s RETURNING id),
     a AS (INSERT INTO asset (tenant_id, area_id, kind, name)
           SELECT %(t)s, id, 'valve', 'FV-101' FROM ar RETURNING id),
     tg AS (INSERT INTO tag (tenant_id, site_id, raw_tag) SELECT %(t)s, id, 'FV-101.ZSC' FROM s RETURNING id),
     m AS (INSERT INTO tag_mapping (tag_id, tenant_id, asset_id, canonical_tag, role, state_true, state_false)
           SELECT tg.id, %(t)s, a.id, 'fv101_closed', 'valve_state', '1', '0' FROM tg, a RETURNING tag_id),
     ep AS (INSERT INTO export_profile (tenant_id, site_id, name) SELECT %(t)s, id, 'PI long' FROM s RETURNING id),
     di AS (INSERT INTO data_import (tenant_id, site_id, export_profile_id, object_key)
            SELECT %(t)s, s.id, ep.id, 'raw/x.csv' FROM s, ep RETURNING id)
INSERT INTO import_report (import_id, tenant_id, total_values, accepted, rejected, duplicates, report, scoring_allowed)
  SELECT id, %(t)s, 10, 8, 1, 1, '{}', true FROM di""",
    "INSERT INTO job (tenant_id, kind) VALUES (%(t)s, 'import')",
    "INSERT INTO audit_event (tenant_id, action) VALUES (%(t)s, 'seed')",
]


@pytest.fixture(scope="session")
def seeded(test_db: TestDB) -> TestDB:
    """Two tenants with exactly one row in every tenant-owned table (seeded as superuser)."""
    with psycopg.connect(test_db.admin_url) as conn:
        for stmt in SEED:
            conn.execute(stmt, {"a": TENANT_A, "b": TENANT_B, "alice": ALICE, "bob": BOB})
        for t in (TENANT_A, TENANT_B):
            for stmt in SEED_TENANT:
                conn.execute(stmt, {"t": t})
    return test_db


@pytest.fixture
def short_tmp() -> Iterator[Path]:
    """A short temp folder for local 'buckets'. pytest's tmp_path is deep, and tenant/site/import
    folders under it can exceed Windows' 260-character path limit."""
    d = Path(tempfile.mkdtemp(prefix="dl_"))
    try:
        yield d
    finally:
        shutil.rmtree(d, ignore_errors=True)


@contextmanager
def tx(url: str, *, tenant_id: uuid.UUID | None = None, user_id: uuid.UUID | None = None) -> Iterator[Any]:
    """Like request_tx (same set_config calls), but ALWAYS rolls back, so tests never affect each other."""
    with psycopg.connect(url, row_factory=dict_row) as conn, conn.transaction(force_rollback=True):
        conn.execute(
            "SELECT set_config('app.user_id', %s, true), set_config('app.tenant_id', %s, true)",
            (str(user_id) if user_id else "", str(tenant_id) if tenant_id else ""),
        )
        yield conn
