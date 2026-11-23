"""Database bootstrap and migrations.

    python -m driplytics_api.db.migrate upgrade      # create/refresh the runtime role, migrate to head
    python -m driplytics_api.db.migrate seed-dev     # local only: demo tenants and users (idempotent)
    python -m driplytics_api.db.migrate current      # show the current revision

Runs with DRIPLYTICS_MIGRATION_DATABASE_URL (the owner/admin role). The runtime role comes
from DRIPLYTICS_DATABASE_URL and must be named driplytics_app (the migrations grant to it).
"""

import argparse
import os
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

import psycopg
from alembic import command
from alembic.config import Config
from psycopg import sql

from driplytics_api.settings import get_settings

APP_ROLE = "driplytics_app"


def migrations_dir() -> Path:
    override = os.environ.get("DRIPLYTICS_MIGRATIONS_DIR")
    # apps/api/src/driplytics_api/db/migrate.py -> apps/api/migrations
    return Path(override) if override else Path(__file__).resolve().parents[3] / "migrations"


def to_sqlalchemy_url(url: str) -> str:
    for prefix in ("postgresql://", "postgres://"):
        if url.startswith(prefix):
            return "postgresql+psycopg://" + url[len(prefix) :]
    return url


def alembic_config(admin_url: str) -> Config:
    cfg = Config()
    cfg.set_main_option("script_location", str(migrations_dir()))
    cfg.set_main_option("sqlalchemy.url", to_sqlalchemy_url(admin_url).replace("%", "%%"))
    return cfg


def ensure_app_role(admin_url: str, app_url: str) -> None:
    """Create or refresh the runtime role: LOGIN, never superuser, never BYPASSRLS."""
    parts = urlsplit(app_url)
    user, password = unquote(parts.username or ""), unquote(parts.password or "")
    if user != APP_ROLE:
        raise SystemExit(f"DRIPLYTICS_DATABASE_URL must use the role '{APP_ROLE}', got '{user}'")
    if not password:
        raise SystemExit("DRIPLYTICS_DATABASE_URL must include a password for the runtime role")
    with psycopg.connect(admin_url, autocommit=True) as conn:
        exists = conn.execute("SELECT 1 FROM pg_roles WHERE rolname = %s", (user,)).fetchone()
        conn.execute(
            sql.SQL(
                "{} ROLE {} WITH LOGIN NOSUPERUSER NOBYPASSRLS NOCREATEDB NOCREATEROLE PASSWORD {}"
            ).format(sql.SQL("ALTER" if exists else "CREATE"), sql.Identifier(user), sql.Literal(password))
        )


def upgrade(admin_url: str, app_url: str, revision: str = "head") -> None:
    ensure_app_role(admin_url, app_url)
    command.upgrade(alembic_config(admin_url), revision)


DEV_SEED = """
INSERT INTO tenant (id, name, slug, plan) VALUES
  ('a1a1a1a1-0000-4000-8000-000000000001', 'Riverbend Water Treatment (synthetic)', 'riverbend', 'pilot'),
  ('b2b2b2b2-0000-4000-8000-000000000002', 'Lakeside Utilities (synthetic)', 'lakeside', 'pilot')
ON CONFLICT (id) DO NOTHING;
-- Subjects are the fixed Keycloak user ids in infra/docker/keycloak/driplytics-realm.json. Keycloak's
-- dev store is not persisted, so a re-created container re-imports the realm; pinning the ids (and
-- re-asserting them here) keeps sign-in working when Postgres outlives Keycloak.
INSERT INTO app_user (email, display_name, idp_subject) VALUES
  ('alice@riverbend.test', 'Alice Riverbend', '0a11ce00-0000-4000-8000-00000000a11c'),
  ('bob@lakeside.test', 'Bob Lakeside', '00000b0b-0000-4000-8000-000000000b0b')
ON CONFLICT (email) DO UPDATE SET idp_subject = EXCLUDED.idp_subject;
INSERT INTO membership (tenant_id, user_id, role)
  SELECT 'a1a1a1a1-0000-4000-8000-000000000001', id, 'owner' FROM app_user WHERE email = 'alice@riverbend.test'
ON CONFLICT DO NOTHING;
INSERT INTO membership (tenant_id, user_id, role)
  SELECT 'b2b2b2b2-0000-4000-8000-000000000002', id, 'owner' FROM app_user WHERE email = 'bob@lakeside.test'
ON CONFLICT DO NOTHING;
INSERT INTO site (tenant_id, name) VALUES
  ('a1a1a1a1-0000-4000-8000-000000000001', 'Riverbend WTP'),
  ('b2b2b2b2-0000-4000-8000-000000000002', 'Lakeside WTP')
ON CONFLICT (tenant_id, name) DO NOTHING;
"""


def seed_dev(admin_url: str) -> None:
    """Demo tenants and users for local development, pre-linked to the fixed Keycloak test users."""
    with psycopg.connect(admin_url, autocommit=False) as conn, conn.cursor() as cur:
        cur.execute(DEV_SEED)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="python -m driplytics_api.db.migrate")
    p.add_argument(
        "action", choices=["upgrade", "downgrade", "current", "seed-dev"], nargs="?", default="upgrade"
    )
    p.add_argument("revision", nargs="?", default=None)
    a = p.parse_args(argv)
    s = get_settings()
    if a.action == "upgrade":
        upgrade(s.migration_database_url, s.database_url, a.revision or "head")
        print("database migrated to", a.revision or "head")
        if s.env == "local":
            seed_dev(s.migration_database_url)
            print("local dev seed applied (Riverbend: alice, Lakeside: bob)")
    elif a.action == "downgrade":
        command.downgrade(alembic_config(s.migration_database_url), a.revision or "-1")
    elif a.action == "current":
        command.current(alembic_config(s.migration_database_url), verbose=True)
    elif a.action == "seed-dev":
        seed_dev(s.migration_database_url)
    return 0


if __name__ == "__main__":
    sys.exit(main())
