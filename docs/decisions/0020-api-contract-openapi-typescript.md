# 0020. API contract: FastAPI response models → committed OpenAPI → generated TypeScript types

- **Status:** Accepted
- **Date:** 2026-11-23

## Context
The web app must call the API with types that match it exactly (architecture: "OpenAPI generated from
FastAPI → generated TypeScript client"). Until P0-13 most routes returned `dict[str, Any]`, so the
OpenAPI document described their responses as free-form objects and a generated client would be untyped.

## Decision
- **Every endpoint declares a response model** (`apps/api/src/driplytics_api/responses.py`). Routes keep
  building dicts from rows; FastAPI validates them against the model, so contract drift fails tests.
  Errors are documented as `ErrorOut {detail}`; operationIds are the route function names.
- **`packages/contracts/openapi.json` is committed**, written by `apps/api/scripts/export_openapi.py`.
- **Types are generated with `openapi-typescript`** into `packages/contracts/src/generated/openapi.ts`
  (committed, never edited by hand). **Requests use `openapi-fetch`** (about 6 kB, no code generation):
  paths, parameters, bodies and responses are all checked by `tsc`. `client.ts` adds the bearer token and
  `X-Tenant-Id` header, `unwrap()` → data or `ApiError`, and friendly names (`Site`, `ImportReport`, …).
- **Staleness is a test failure on both sides:** `test_openapi_contract.py` (pytest) fails if
  `openapi.json` differs from the running API or any 2xx response is untyped; `pnpm test` in
  `packages/contracts` runs `generate.mjs --check`. One command regenerates both: `.\tasks.ps1 contracts`.

## Consequences
- Changing an API response means: edit the model, run `.\tasks.ps1 contracts`, commit the two generated
  files. The TypeScript compiler then points at every screen that needs updating.
- Alternatives considered: hand-written types (drift), `orval`/`@hey-api/openapi-ts` (generate a lot of
  code per endpoint; more to review). The connector's ingest contract (Go, Phase 3) reuses the same
  `openapi.json`.
