# 0003. Tenant isolation: shared database with row-level security

- **Status:** Accepted
- **Date:** 2026-11-22
- **Answers:** Q2 in `docs/questions.md`

## Decision
- One PostgreSQL database and schema. Every tenant-owned table has a non-null `tenant_id`.
- **Postgres row-level security** on every tenant-owned table: `USING (tenant_id = current_setting('app.tenant_id')::uuid)`, with `FORCE ROW LEVEL SECURITY`.
- The API sets `app.tenant_id` with `SET LOCAL` at the start of each request transaction. The app's database role is not a superuser and does not have `BYPASSRLS`.
- Background jobs carry the tenant ID and set it the same way.
- Time-series files are partitioned by `tenant=<id>/` in object storage; the storage layer refuses paths outside the current tenant.
- Partner users access a client tenant only through an explicit `partner_access` grant, which is audited.

## Escape hatch
A contract that requires stronger isolation gets a dedicated database (same schema, separate connection string) or on-prem deployment (mode C). No code changes needed.

## Consequences
Cheapest to operate, with isolation enforced by the database rather than application code. **Required:** a cross-tenant test suite in CI (tenant A can never read, update or delete tenant B's data through any endpoint or job), plus a migration lint that fails if a new table has `tenant_id` but no RLS policy.
