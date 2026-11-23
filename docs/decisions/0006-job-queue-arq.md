# 0006. Job queue: Arq on Redis

- **Status:** Accepted
- **Date:** 2026-11-22

## Decision
Background jobs (imports, checks, reports, emails) run on **Arq** with Redis. Jobs are idempotent (keyed by import or check-run ID), retried with backoff, time-limited, and report progress to Postgres for the UI. Scheduled jobs are triggered through an authenticated HTTP endpoint called by Cloud Scheduler now and EventBridge later (ADR 0007).

## Consequences
Simple and async-native, matching FastAPI. If we later need complex multi-step workflows, revisit with Celery or Temporal.
