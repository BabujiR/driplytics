# 0002. Monorepo and tooling

- **Status:** Accepted
- **Date:** 2026-11-22

## Decision
One repository with `apps/web`, `apps/api`, `services/worker`, `engine/`, `connector/` (Go, Phase 3), `packages/ui`, `packages/contracts`, `infra/`, `docs/`.
- **Python:** `uv` workspaces, Ruff (lint + format), mypy (strict for new code), pytest.
- **TypeScript:** pnpm workspaces + Turborepo, ESLint, Prettier, Vitest, Playwright.
- **Go (Phase 3):** its own module in `connector/`, golangci-lint, govulncheck.
- A root `Makefile` with `dev`, `test`, `lint`, `seed`, `bench`.

## Consequences
One CI pipeline and one place for API contracts, and AI agents see the whole system. Requires path-based CI filters so builds stay fast.
