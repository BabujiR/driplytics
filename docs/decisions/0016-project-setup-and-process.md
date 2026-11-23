# 0016. Brand placeholder, domain, repository and solo-founder process

- **Status:** Accepted
- **Date:** 2026-11-22
- **Answers:** Q10 in `docs/questions.md`

## Decision
- **Brand:** placeholder design tokens (water-blue primary on neutral slate) until a professional logo after the first pilot.
- **Domain:** `driplytics.com`, with `app.` for the web app, `api.` for the API, `ingest.` for connectors, and Postmark for transactional email from `notify.driplytics.com`. **Register the domain now if not already done.**
- **Repository:** private GitHub repository `driplytics`, CI and deployment on GitHub Actions.
- **Process (solo founder + AI agents):** the main branch is protected; merges need passing CI (lint, types, tests, cross-tenant isolation suite, portability check), with no human review requirement. Conventional commit messages. Every significant decision gets an ADR.
