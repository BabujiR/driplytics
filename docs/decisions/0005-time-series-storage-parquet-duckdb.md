# 0005. Time-series storage: partitioned Parquet in object storage, queried with DuckDB

- **Status:** Accepted
- **Date:** 2026-11-22

## Decision
- Clean series are stored as Parquet (zstd), partitioned `tenant=<id>/site=<id>/tag=<canonical>/month=YYYY-MM/`.
- Checks and chart queries read with **DuckDB** (in the worker and API processes). Charts get server-side LTTB downsampling.
- Corrections are written as new partition files plus a manifest pointer swap; never in-place edits.
- Raw uploads are immutable objects kept per ADR 0013.

## Consequences
Very cheap storage, the same on GCS, S3 and MinIO, and it fits the existing engine. Revisit (TimescaleDB or ClickHouse) if interactive queries across thousands of tags at once become slow. Measure that before deciding.
