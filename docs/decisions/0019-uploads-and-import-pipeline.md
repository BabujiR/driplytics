# 0019. Uploads go straight to storage; one import = one worker job

- **Status:** Accepted
- **Date:** 2026-11-23

## Context
Historian exports can be several GB (a year of 100 tags at 10 s is ~15 GB of CSV). They must not
stream through the API process, imports must survive retries and duplicate job delivery, and every
step must stay inside the tenant's row-level security.

## Decision
- **Upload:** `POST /sites/{id}/imports` creates the import (`pending`) and returns an S3-style
  **presigned PUT URL**; the browser uploads straight to the bucket. Signing uses botocore against an
  S3-compatible endpoint (MinIO locally, S3 on AWS, Google Cloud Storage via its S3-interoperable XML API
  with HMAC keys), so the same code works on every target cloud (ADR 0007). It is the only module allowed
  to import a cloud SDK (`scripts/check_portability.py`).
- **Object keys:** `tenant=<t>/site=<s>/imports/<import_id>/<safe filename>` in the raw bucket; clean
  output in `tenant=<t>/site=<s>/imports/<import_id>/values/<canonical_tag>.parquet` in the data bucket,
  plus `import_report.json`. (ADR 0005's month partitioning applies when continuous connector data
  arrives in Phase 3; uploads are naturally partitioned by import.)
- **Start:** `POST /imports/{id}/start` verifies the object exists, marks `queued` and enqueues the Arq job
  with `_job_id = import:<id>`, so double clicks don't queue twice.
- **Job:** runs in the worker as the runtime role with the tenant context. It only proceeds from `queued`
  (a duplicate delivery is skipped), writes progress at most every 2 s, saves the report (the database
  re-checks the counts balance), registers every raw tag seen, and audits success or failure. Errors mark
  the import `failed` with the message and are not auto-retried; the user restarts it.
- **Mappings for Phase 0:** a `tag_mapping.csv` upload (validated by the engine) fills `tag_mapping` until
  the Mapping Assistant arrives in Phase 1.

## Consequences
- The Phase 0 exit demo is a test (`apps/api/tests/db/test_import_pipeline.py`) and a script
  (`.\tasks.ps1 demo`).
- Full rejected-row export is not stored yet; the report keeps up to 20 examples per reason
  (`/imports/{id}/rejected-examples.csv`).
- Files are limited to 5 GB for now (the S3 single-PUT limit). Multipart uploads for bigger files are a
  follow-up (presigned part URLs + complete), tracked as P0-17b; split larger exports by month meanwhile.
