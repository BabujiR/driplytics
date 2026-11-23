# 0018. Database access: psycopg at runtime, SQL-file migrations through Alembic

- **Status:** Accepted
- **Date:** 2026-11-23

## Context
Phase 0 needs migrations (P0-06), strict tenant isolation (ADR 0003) and a small number of queries.
Row-level security depends on per-transaction settings (`app.tenant_id`, `app.user_id`), which must
be set on exactly the connection and transaction that runs the query.

## Decision
- **Runtime:** plain **psycopg 3** with `dict_row`. All tenant-data access goes through
  `driplytics_api.db.request_tx(url, user_id=..., tenant_id=...)`, which opens one transaction and sets
  the context with `set_config(..., is_local => true)`. No ORM for now: queries are few, explicit and
  easy to review for tenant safety.
- **Migrations:** **Alembic** for ordering and version tracking, with each migration's DDL in a plain
  `.up.sql` / `.down.sql` file next to it. The SQL can be read, reviewed and tested directly with psql.
- **Roles:** migrations run as the owner role (`DRIPLYTICS_MIGRATION_DATABASE_URL`, used only by the
  one-shot `migrate` container). The API and worker use `driplytics_app` (`DRIPLYTICS_DATABASE_URL`),
  which is created/refreshed by `python -m driplytics_api.db.migrate upgrade` as LOGIN, NOSUPERUSER,
  NOBYPASSRLS.
- **Guard rails in the schema itself:** composite `(id, tenant_id)` foreign keys so rows can't reference
  another tenant's parent; `import_report` enforces `accepted + rejected + duplicates = total_values`;
  `audit_event` is append-only for the runtime role.
- **Guard rails in CI:** `apps/api/tests/db/test_schema_lint.py` fails if any new table lacks forced
  RLS and a policy (unless explicitly listed as global).

## Consequences
- Tenant safety is enforced by PostgreSQL, not by remembering a `WHERE tenant_id = ...` clause.
- Connection pooling (psycopg_pool) is a later optimization; the transaction-local context is already
  pool-safe (tested).
- If query volume grows, SQLAlchemy Core can be added for query building without changing the
  migration or RLS approach.
