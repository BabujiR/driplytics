# Phase 0 task list (weeks 1–2)

Estimates are in focused days for one developer working with an AI coding agent. All questions are answered (see `docs/decisions/`). Remaining "blocked by" entries are ordinary task dependencies.

| ID | Task | Depends on | Est. | Status |
|---|---|---|---|---|
| P0-01 | Create monorepo skeleton (folders from the design note §2), root Makefile, `.editorconfig`, README | — | 0.5 | ✅ done (verify locally: `.\tasks.ps1 install`, `test`, `dev`) |
| P0-02 | Python workspace with `uv`: `apps/api`, `services/worker`, `engine` as members; Ruff + mypy config | P0-01 | 0.5 | ✅ done (verify locally: `.\tasks.ps1 install`, `test`, `dev`) |
| P0-03 | JS workspace with pnpm + Turborepo: `apps/web`, `packages/ui`, `packages/contracts`; ESLint, Prettier, Vitest | P0-01 | 0.5 | ✅ done (verify locally: `.\tasks.ps1 install`, `test`, `dev`) |
| P0-04 | Docker Compose: Postgres 16, Redis, MinIO, Mailpit, Keycloak (dev auth), API, worker, web; health checks; `make dev` | P0-02, P0-03 | 1.0 | ✅ done (verify locally: `.\tasks.ps1 install`, `test`, `dev`) |
| P0-05 | Engine housekeeping: rename to `driplytics_engine`, fsspec/S3 paths, progress callback; all tests still pass | P0-02 | 0.5 | ✅ done: `driplytics_engine`, object-storage paths (fsspec), progress callback, Ruff clean |
| P0-06 | Database migrations (Alembic) for the Phase 0 tables + row-level security policies | P0-04 | 1.0 | ✅ done: schema + forced RLS verified on PostgreSQL 16; `migrate` service; dev seed (ADR 0018) |
| P0-07 | Cross-tenant isolation test suite (runs in CI) | P0-06 | 0.5 | ✅ done: `apps/api/tests/db/` isolation + schema lint (run with the stack up: `.\tasks.ps1 test-db`) |
| P0-08 | Auth: OIDC login, session handling, `/me`, role checks, membership model | P0-06 | 1.5 | ✅ API done: OIDC verify, provisioning, `/api/v1/me`, tenant + role checks. Web sign-in screen → P0-16 |
| P0-09 | Audit log service + middleware (who, what, before/after) | P0-06 | 0.5 | ✅ done: `audit.record()` in every mutating endpoint (same transaction), `GET /api/v1/audit` (admin+) |
| P0-10 | Site CRUD endpoints + export profile model | P0-08 | 0.5 | ✅ done: sites + export profiles CRUD, `tag_mapping.csv` upload validated by the engine |
| P0-11 | Upload flow: presigned multipart URLs, import record, `start` endpoint | P0-10 | 1.0 | ✅ done: presigned direct uploads, start/status/list/report/examples (ADR 0019) |
| P0-12 | Arq worker: `import_file` job, Parquet partition writer, report storage, progress events | P0-05, P0-11 | 1.5 | ✅ done: Arq `import_file` job; end-to-end test + `.\tasks.ps1 demo` |
| P0-13 | OpenAPI export + generated TypeScript client in `packages/contracts` | P0-10 | 0.5 | blocked by P0-10 |
| P0-14 | Design tokens (light/dark, density modes) + Tailwind config + white-label token override | P0-03 | 1.0 | ready (ADR 0008, 0016) |
| P0-15 | Storybook with base components (Button, Input, Table, Chip, Card, Banner, Stat, EmptyState, Skeleton, Dialog, Toast) + states | P0-14 | 2.0 | ready |
| P0-16 | App shell: sidebar navigation, top bar, site switcher, Cmd+K placeholder, theme toggle | P0-15 | 1.0 | ready |
| P0-17 | Upload screen (drag and drop, format detection preview, progress) | P0-13, P0-16 | 1.0 | blocked by P0-13 |
| P0-18 | Import report screen (balanced stacked bar, reasons table, examples, rejected CSV) | P0-17 | 1.0 | blocked by P0-17 |
| P0-19 | Demo tenant seeder: "Riverbend Water Treatment (synthetic)", 30 days, mapping, one import | P0-12 | 0.5 | blocked by P0-12 |
| P0-20 | CI pipeline: lint, types, unit tests, engine smoke benchmark, Playwright upload→report, axe | P0-18 | 1.0 | ✅ done: `.github/workflows/ci.yml` (Python + DB isolation, web build, compose) |
| P0-21 | ADRs 0001–0016 | answers | 0.5 | ✅ done (0001–0016) |
| P0-23 | Terraform `infra/terraform/gcp/`: Cloud Run (api, worker, web), Cloud SQL Postgres, Cloud Storage, Memorystore Redis, Secret Manager, Artifact Registry; GitHub Actions deploy via Workload Identity Federation | P0-04 | 1.5 | ready (ADR 0007) |
| P0-24 | CI portability check: fail on `google.cloud` imports outside `infra/`; storage only through the fsspec `Storage` interface | P0-02 | 0.25 | ✅ done: `scripts/check_portability.py` runs in CI |
| P0-22 | Wireframe review session → update wireframes and §12 if needed | your feedback | 0.5 | **waiting on you** |

**Total:** about 20 focused days (including the GCP environment). With an AI agent and some tasks in parallel, it fits the 2-week Phase 0 window. If it slips, cut P0-19 (seeder) and P0-20's Playwright test first; never cut P0-07 (isolation tests).

## Phase 0 exit demo (about 10 minutes)

1. `make dev` on a clean machine → all services healthy.
2. Sign in as two users in two tenants; show tenant B can't see tenant A's site.
3. Upload `historian_long.csv` → live progress → import report: **5,179 = 5,157 + 19 + 3**, rejection reasons, unmapped-tag banner.
4. Switch to dark mode and compact density; open Storybook.
5. Show CI green on a pull request.
