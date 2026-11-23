# 0007. Cloud provider: GCP for demo and trials, built to move to AWS

- **Status:** Accepted
- **Date:** 2026-11-22
- **Answers:** Q1 in `docs/questions.md`

## Context
Driplytics needs a low-cost cloud for demos and early trials. The founder plans to move to AWS once the product is proven (for AWS Marketplace, enterprise buyer familiarity, and the broader managed-service catalogue). The risk is GCP-specific code and infrastructure creeping in and making that move expensive.

## Decision
Run demo, staging and trial environments on **Google Cloud (region `us-east1` or `us-central1`, US-only data)**. Build everything against **portable, open interfaces** so the AWS migration is a planned infrastructure change with no application rewrite.

### Service mapping (use only services that have a direct AWS equivalent)

| Need | GCP now | AWS later | Portable interface in our code |
|---|---|---|---|
| Containers (API, worker, web) | Cloud Run | ECS on Fargate (or App Runner) | Docker images + environment variables only |
| PostgreSQL 16 | Cloud SQL for PostgreSQL | RDS for PostgreSQL | Standard Postgres + SQLAlchemy/Alembic; only standard extensions |
| Object storage (raw files, Parquet) | Cloud Storage | S3 | `fsspec` URLs (`gs://` → `s3://`) behind a `Storage` interface |
| Redis (job queue) | Memorystore for Redis | ElastiCache for Redis | Redis protocol only |
| Secrets | Secret Manager | Secrets Manager | Injected as environment variables at deploy time |
| Container registry | Artifact Registry | ECR | Standard OCI images |
| Scheduled jobs | Cloud Scheduler → HTTP endpoint | EventBridge Scheduler → same endpoint | An authenticated HTTP job trigger in our API |
| Load balancer + WAF | Cloud Load Balancing + Cloud Armor | ALB + AWS WAF | — |
| Email | Postmark (third party) | Postmark (unchanged) | SMTP/API, independent of the cloud |
| Logs, traces, metrics | Cloud Logging / Trace via **OpenTelemetry** | CloudWatch / X-Ray via **OpenTelemetry** | OpenTelemetry SDK only; no vendor logging SDKs |
| Infrastructure as code | Terraform `infra/terraform/gcp/` | Terraform `infra/terraform/aws/` | Same module inputs and outputs for both clouds |
| CI/CD | GitHub Actions → GCP via Workload Identity Federation | GitHub Actions → AWS via OIDC role | No long-lived cloud keys in CI |

### Portability rules (enforced in code review and CI)
1. **No GCP-only services** in the product path: no Pub/Sub, BigQuery, Firestore, Spanner, AlloyDB, Cloud Functions, Vertex AI, or Google client libraries in application code. A CI check fails the build on any `google.cloud` import outside `infra/`.
2. **All cloud-specific values come from environment variables** (bucket URL, database URL, Redis URL, secrets).
3. **Storage access only through the `Storage` interface** (fsspec), so switching between `gs://` and `s3://` is configuration.
4. **Containers stay stateless**: everything lives in Postgres, object storage or Redis.
5. **The local Docker Compose environment (MinIO, Postgres, Redis) stays the reference**: if it works locally, it works on either cloud.
6. **The edge connector's ingest URL is a DNS name we control** (`ingest.driplytics.com`), never a cloud-provider URL. Customers' connectors won't need reconfiguring when we move.

## Consequences
- **Low cost now:** Cloud Run scales to zero between demos; new GCP accounts get free credits.
- **A small, planned migration later**, roughly 1–2 weeks:
  1. Apply `infra/terraform/aws/`.
  2. Copy object storage with Storage Transfer Service or rclone.
  3. Migrate Postgres with `pg_dump`/`pg_restore` or AWS DMS for a near-zero-downtime cutover.
  4. Switch the DNS for `app.` and `ingest.` subdomains.
  5. Keep GCP read-only for 30 days as a fallback, then delete.
- **Customer data on GCP:** trial agreements must list Google Cloud as a sub-processor and state that hosting may move to AWS with notice. Do this before the first trial with real customer data.
- We give up GCP-only conveniences (BigQuery for internal analytics, Pub/Sub). That's acceptable at this stage.
- Phase 0 adds two tasks: `infra/terraform/gcp/` (a minimal demo environment) and the CI portability check. `infra/terraform/aws/` is written at migration time, against the same module interface.

## Options considered
- **AWS from day one:** the cleanest long-term path, but the founder prefers GCP for demos and trials.
- **GCP long-term:** possible, but this decision keeps the AWS move open at low cost.
- **Use GCP-native services fully now:** faster to start, but it would make the migration a rewrite. Rejected.
