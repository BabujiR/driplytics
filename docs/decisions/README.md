# Architecture decision records

Read these before starting any work. **Where an ADR differs from a default in `CLAUDE.md`, the ADR wins.**

| # | Decision | Status |
|---|---|---|
| [0001](0001-record-architecture-decisions.md) | Record architecture decisions as ADRs | Accepted |
| [0002](0002-monorepo-and-tooling.md) | Monorepo; uv/Ruff/mypy, pnpm/Turborepo, Go module for the connector | Accepted |
| [0003](0003-tenancy-isolation-row-level-security.md) | Shared Postgres + `tenant_id` + row-level security, with a dedicated-DB escape hatch | Accepted |
| [0004](0004-authentication-oidc-workos-keycloak.md) | OIDC; WorkOS in the cloud, Keycloak locally and on-prem; roles in our DB | Accepted |
| [0005](0005-time-series-storage-parquet-duckdb.md) | Partitioned Parquet in object storage, queried with DuckDB | Accepted |
| [0006](0006-job-queue-arq.md) | Arq on Redis for background jobs | Accepted |
| [0007](0007-cloud-provider-gcp-first-portable-to-aws.md) | GCP for demo and trials, built to move to AWS | Accepted |
| [0008](0008-design-system.md) | Tailwind + shadcn/ui + design tokens + Storybook | Accepted |
| [0009](0009-first-historian-pi-web-api.md) | PI first (export profiles, then PI Web API in the connector); OPC UA second | Accepted |
| [0010](0010-pricing-and-plans.md) | Pilot (creditable), Starter 500 / Pro 2,000 / Enterprise 10,000+ mapped tags | Accepted |
| [0011](0011-first-target-segment.md) | Municipal water and wastewater first; food and beverage second | Accepted |
| [0012](0012-display-units.md) | Per-site display units, US customary by default | Accepted |
| [0013](0013-data-retention.md) | Raw 2 years, clean series 5 years, purge 30 days after leaving | Accepted |
| [0014](0014-llm-policy-mapping-assistant.md) | Claude via API, metadata only, off by default on-prem | Accepted |
| [0015](0015-product-default-worklist-top-10.md) | Worklist shows the top 10 by default | Accepted |
| [0016](0016-project-setup-and-process.md) | Placeholder brand, driplytics.com, GitHub Actions, CI-gated merges | Accepted |
| [0017](0017-local-s3-chainguard-minio.md) | Local S3: Chainguard MinIO image; API creates buckets in dev | Accepted |
| [0018](0018-database-access-psycopg-and-sql-migrations.md) | psycopg at runtime; Alembic with SQL-file migrations; owner vs runtime DB roles | Accepted |
| [0019](0019-uploads-and-import-pipeline.md) | Presigned direct-to-storage uploads; one import = one idempotent worker job | Accepted |
| [0020](0020-api-contract-openapi-typescript.md) | Response models → committed OpenAPI → openapi-typescript types + openapi-fetch client | Accepted |
| [0021](0021-web-sign-in-and-api-proxy.md) | Web sign-in: server-side OIDC + PKCE, encrypted cookie session, same-origin API proxy | Accepted |
