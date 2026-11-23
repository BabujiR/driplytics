# Driplytics

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
| Web app | http://localhost:3000 | (shows live stack status in Phase 0) |
| API docs | http://localhost:8000/api/docs | — |
| API readiness | http://localhost:8000/health/ready | — |
| MinIO console (object storage) | http://localhost:9001 | driplytics / driplytics-dev-secret |
| Mailpit (local email inbox) | http://localhost:8025 | — |
| Keycloak (local sign-in) | http://localhost:8080 | admin / admin-dev · test users `alice`, `bob` / `Passw0rd!dev` |
| Postgres | localhost:5432 | driplytics / driplytics-dev |

All passwords above are **local development defaults only**.

If PowerShell blocks the script: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.

## Project status

**Phase 0 (foundations) in progress.** P0-01 to P0-04 are done: monorepo, Python and JS workspaces, Docker Compose stack. Next: P0-05 to P0-08 (engine housekeeping, database + row-level security, auth).

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

