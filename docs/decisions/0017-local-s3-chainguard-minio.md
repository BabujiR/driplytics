# 0017. Local S3 storage: Chainguard MinIO image, buckets created by the API in dev

- **Status:** Accepted
- **Date:** 2026-11-23

## Context
The local stack used `minio/minio` and a one-shot `minio/mc` container to create buckets. MinIO removed both images
from Docker Hub in September 2026, and quay.io stopped anonymous pulls the same month, so `docker compose up` failed.

## Decision
- Use **`cgr.dev/chainguard/minio`** (free, maintained, S3-compatible) as the local object store.
- It runs as uid 65532 and is distroless (no shell), so in **local dev only** we run it as root (`user: "0:0"`) to
  write the named volume, and it has no in-container health check.
- **Remove the `minio-init` container.** With `DRIPLYTICS_STORAGE_AUTO_CREATE_BUCKETS=true` (set only in `compose.yaml`),
  the API's readiness check creates missing buckets through the same fsspec storage layer. The API container's
  health check (`/health/ready`) therefore also covers storage.
- Cloud environments (GCS now, S3 later) never auto-create: buckets come from Terraform.

## Consequences
- No dependency on MinIO-published images. If Chainguard's free tier changes, alternatives that speak the same S3 API
  are SeaweedFS, Garage, RustFS or VersityGW, and only `compose.yaml` changes.
- The MinIO web console in the community build is a basic object browser only.
