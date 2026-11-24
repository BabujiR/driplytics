# Driplytics

[![CI](https://github.com/BabujiR/driplytics/actions/workflows/ci.yml/badge.svg)](https://github.com/BabujiR/driplytics/actions/workflows/ci.yml)

**In-plant water and energy loss detection from historian data.**
No new sensors, no data scientist: findings ranked in dollars.

## 🔗 Live demo

| What | Link |
|---|---|
| **Wireframes (Phase 0, low-fidelity)** | **https://storage.googleapis.com/driplytics-demo/index.html** |

The wireframes cover the five key screens: onboarding wizard, worklist (home), finding detail, import report and mapping assistant. Click the tabs at the top; the yellow notes explain each numbered element. All data shown is synthetic.

The source is in [`docs/wireframes/index.html`](docs/wireframes/index.html). To publish an updated version:

```bash
gcloud storage cp docs/wireframes/index.html gs://driplytics-demo/index.html --content-type="text/html" --cache-control="no-cache"
```

## Getting started (local development)

**Prerequisites:** [Docker Desktop](https://www.docker.com/products/docker-desktop/), [uv](https://docs.astral.sh/uv/) (Python), Node.js 22+ (pnpm is installed automatically by `install`: via corepack on Node 22–24, or `npm install -g pnpm@10` on Node 25+), Git.

```powershell
# Windows PowerShell (macOS/Linux/WSL: use `make <target>` with the same names)
copy .env.example .env      # optional: every setting has a working default
.\tasks.ps1 install          # uv sync --all-packages + pnpm install
.\tasks.ps1 test             # Python + JS tests
.\tasks.ps1 dev              # start the whole stack with Docker Compose
```

When the stack is healthy (`.\tasks.ps1 ps` shows every service as *healthy*):

| Service | URL | Login |
|---|---|---|
| Web app | http://localhost:3000 | `alice` or `bob` / `Passw0rd!dev` (Keycloak sign-in) · stack status: http://localhost:3000/status |
| API docs | http://localhost:8000/api/docs | — |
| API readiness | http://localhost:8000/health/ready | — |
| MinIO console (object storage) | http://localhost:9001 | driplytics / driplytics-dev-secret |
| Mailpit (local email inbox) | http://localhost:8025 | — |
| Keycloak (local sign-in) | http://localhost:8080 | admin / admin-dev · test users `alice`, `bob` / `Passw0rd!dev` |
| Postgres | localhost:5432 | driplytics / driplytics-dev |

All passwords above are **local development defaults only**.

**Run the Phase 0 demo end to end** (stack running): `.\tasks.ps1 demo` signs in as alice, uploads the tag
mapping, uploads a historian export straight to object storage, runs the import on the worker and prints
`5,179 = 5,157 accepted + 19 rejected + 3 duplicates`. Pass your own file:
`uv run python apps/api/scripts/dev_import.py my_export.csv --mapping my_tags.csv`.

**Design system:** `.\tasks.ps1 storybook` opens every component and state at http://localhost:6006
(toolbar: light/dark theme, comfortable/compact density; the Accessibility tab runs axe).

**Before pushing:** `.\tasks.ps1 check` runs what CI runs (lint, strict types, portability, all tests).

**Try sign-in end to end** (stack running): `.\tasks.ps1 token` signs in to Keycloak as `alice`, calls
`GET /api/v1/me`, then `GET /api/v1/tenants/current` for her organization (Riverbend, synthetic).
Use `uv run python apps/api/scripts/dev_token.py bob --tenant` for the Lakeside user.

**Database:** the one-shot `migrate` container applies migrations and seeds the two demo tenants before the
API starts. The API and worker connect as `driplytics_app`, which row-level security applies to (ADR 0003, 0018).
Run `.\tasks.ps1 test-db` for the cross-tenant isolation tests (they create and drop their own database).

If PowerShell blocks the script: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.

## Project status

**Phase 0 (foundations) in progress.** Done: P0-01 to P0-16, P0-20, P0-24: workspaces, Docker stack,
engine, schema with row-level security, isolation tests, sign-in and roles, audit log, sites and export
profiles, direct-to-storage uploads, the worker import job, the typed API client, the design system with
Storybook, and the signed-in app shell. CI and the portability check run on every push.
Next: the upload screen (P0-17) and the import report screen (P0-18).

**Changing the API?** Run `.\tasks.ps1 contracts` and commit `packages/contracts/openapi.json` and
`packages/contracts/src/generated/openapi.ts`; tests fail until they match the API (ADR 0020).

## Repository guide

| Path | What's there |
|---|---|
| [`CLAUDE.md`](CLAUDE.md) | Master build prompt and product spec (read this first) |
| [`docs/decisions/`](docs/decisions/README.md) | Architecture decision records (ADRs). These override defaults in `CLAUDE.md` |
| [`docs/architecture.md`](docs/architecture.md) | System diagram and component responsibilities |
| [`docs/phase0/design-note.md`](docs/phase0/design-note.md) | Phase 0 scope, data model, interfaces, risks |
| [`docs/phase0/tasks.md`](docs/phase0/tasks.md) | Phase 0 task list with estimates and dependencies |
| [`docs/questions.md`](docs/questions.md) | The 10 design questions and the decisions taken |
| [`docs/wireframes/`](docs/wireframes/index.html) | Low-fidelity wireframes (also live at the demo link above) |
| [`apps/api/`](apps/api) | FastAPI service (health, readiness, version in Phase 0) |
| [`apps/web/`](apps/web) | Next.js web app |
| [`services/worker/`](services/worker) | Arq background worker |
| [`packages/ui/`](packages/ui) · [`packages/contracts/`](packages/contracts) | Design system · shared API types |
| [`engine/`](engine/README.md) | Python import engine and leak-by check, with tests and synthetic fixtures |
| [`compose.yaml`](compose.yaml) · [`infra/`](infra) | Local stack · Dockerfiles, Keycloak realm, Terraform (later) |

## Key decisions at a glance

- **Cloud:** GCP for demo and trials, built to move to AWS ([ADR 0007](docs/decisions/0007-cloud-provider-gcp-first-portable-to-aws.md))
- **Stack:** Python (FastAPI, engine, workers) · Next.js + Tailwind + shadcn/ui · Go edge connector (Phase 3)
- **Data:** PostgreSQL with row-level security · Parquet + DuckDB for time series
- **First market:** municipal water and wastewater; food and beverage second

