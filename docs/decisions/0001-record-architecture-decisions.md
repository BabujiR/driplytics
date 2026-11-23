# 0001. Record architecture decisions

- **Status:** Accepted
- **Date:** 2026-11-22

## Context
Driplytics will be built largely with AI coding agents over many sessions. Decisions made in one session must be visible in the next, and to any future team member, together with the reasons behind them.

## Decision
We record every significant, hard-to-reverse decision as an Architecture Decision Record (ADR) in `docs/decisions/`, numbered sequentially, using this format: Status, Date, Context, Decision, Consequences, and the options considered.

An ADR is required for: cloud provider, tenancy model, auth vendor, storage engines, queue, major libraries, public API changes, security-relevant choices, and anything `CLAUDE.md` says to "write an ADR" for. ADRs are never edited after acceptance; a new ADR supersedes an old one.

## Consequences
- Agents read `CLAUDE.md` and `docs/decisions/` before starting work, which keeps sessions consistent.
- Small overhead per decision (about 10 minutes), much less than re-debating decisions later.

## Planned ADRs (Phase 0)
0002 Monorepo and tooling · 0003 Tenancy isolation · 0004 Authentication · 0005 Time-series storage · 0006 Job queue · 0007 Cloud provider and regions · 0008 Design system
