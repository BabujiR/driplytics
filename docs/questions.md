# Questions for you (answers change the design)

> **All 10 answered on 2026-11-22.** See `docs/decisions/README.md`. The options below are kept for the record.

Answer in any form, even just "Q1: A". Each question has my **recommended default**. If you're unsure, say "default" and I'll record the choice in an ADR. **Q1–Q3 block Phase 0. Q4–Q10 block Phase 1.**

---

### Q1. Cloud provider? ✅ **Decided: GCP for demo and trials, built to move to AWS later (ADR 0007).**
- **A. AWS** *(recommended)*: the broadest managed services (RDS, S3, ECS/Fargate), the most common choice for industrial SaaS, and AWS Marketplace as a future sales channel.
- **B. Azure**: many utilities and manufacturers are Microsoft shops (Entra ID, Azure Government), which can ease procurement. A strong choice if your first customers run Microsoft.
- **C. GCP**: good, but less common with this customer base.

*Also:* is **US-only data residency** fine for year one (single region, us-east), or do you expect Canadian or EU customers soon?

### Q2. Tenant isolation model? ✅ **Decided: Shared database + row-level security (ADR 0003).**
- **A. Shared database + `tenant_id` + Postgres row-level security** *(recommended)*: the cheapest to run, with isolation enforced by the database itself and tested in CI.
- **B. Schema per tenant**: stronger separation, but migrations get heavier as tenant count grows.
- **C. Database per tenant**: the strongest, and the most expensive operationally.

*Recommended path:* A by default, plus the ability to put a specific large customer on a dedicated database (or mode C, on-prem) if a contract requires it.

### Q3. Authentication / SSO vendor? ✅ **Decided: OIDC; WorkOS in the cloud, Keycloak locally and on-prem (ADR 0004).**
- **A. WorkOS** *(recommended for SaaS)*: enterprise SSO (Entra ID, Okta, SAML) and directory sync priced per connection, with a free tier for email/password. Fast to integrate.
- **B. Auth0 / Clerk**: polished, but enterprise SSO gets expensive per connection.
- **C. Keycloak (self-hosted)**: free, and the same software works for on-prem (mode C), but we have to operate it.

*Recommended path:* code against a standard OIDC interface; use **WorkOS in the cloud and Keycloak for on-prem and local development**.

### Q4. First historian for the Go edge connector? ✅ **Decided: PI first, then OPC UA (ADR 0009).**
- **A. AVEVA/OSIsoft PI via PI Web API** *(recommended)*: the most common historian in water, power and process plants, with a clean REST API.
- **B. OPC UA**: universal, and a good second.
- **C. AspenTech IP.21**: common in chemicals and refining, less so in water.

*Do you have a likely first customer? Their historian should win.*

### Q5. Pricing tiers: boundaries and what counts as a "tag"? ✅ **Decided: Proposal accepted; pilot fee creditable; savings-share later (ADR 0010).**
Proposal:

| Plan | Mapped tags | Price (per site, per month, billed annually) |
|---|---|---|
| Pilot | up to 2,000 | $5k–15k one-time, 30 days |
| Starter | 500 | $1,000 |
| Professional | 2,000 | $2,500 |
| Enterprise | 10,000+ | from $5,000, custom |

- **Count only *mapped* tags** *(recommended)*. Unmapped or ignored tags are free, so customers aren't punished for messy historians.
- Are these numbers OK? Do you also want the **outcome-based option** (a share of verified savings) available from launch, or later?

### Q6. First target segment for templates, demo data and messaging? ✅ **Decided: Municipal water/wastewater first, food and beverage second (ADR 0011).**
- **A. Municipal water and wastewater treatment plants** *(recommended)*: matches the demo tenant and the leak-by story, with clear $/kgal costs.
- **B. Food and beverage**
- **C. Power plants**
- **D. Pulp and paper**

### Q7. Units for display? ✅ **Decided: Per-site, US customary by default (ADR 0012).**
- **A. Per-site setting, defaulting to US customary** (gpm, gal, psi, °F) for US sites *(recommended)*. Storage stays in canonical units.
- **B. SI everywhere** (m³/h, kPa, °C)

### Q8. Data retention defaults? ✅ **Decided: Raw 2 years, clean 5 years, purge 30 days after leaving (ADR 0013).**
- **Raw uploaded files:** 2 years *(recommended)*.
- **Clean time series:** 5 years *(recommended)*, so a full baseline plus savings verification is possible.
- **Deleted tenant data:** purged within 30 days.

Customers can shorten these in their contract. OK?

### Q9. LLM provider and data policy for the mapping assistant? ✅ **Decided: Claude, metadata only, off by default on-prem (ADR 0014).**
- **Provider:** Anthropic Claude via API *(recommended)*, behind an interface so it can be swapped or disabled.
- **Policy:** send only **tag names, descriptions, engineering units and summary statistics**, never raw time series. A tenant-level on/off switch that is **off by default for on-prem** and **on by default for SaaS**, disclosed in the terms.

Agree?

### Q10. Brand assets and practical setup? ✅ **Decided: Placeholder brand, driplytics.com, GitHub Actions, CI-gated merges (ADR 0016).**
- Do you have a **logo or brand color**? If not, I'll use a placeholder (a water-blue primary on a neutral slate base) in the design tokens, easy to replace later.
- Is **driplytics.com registered**? I'll use it for transactional email (via Postmark or AWS SES) and the app URL (`app.driplytics.com`).
- **GitHub:** create a private repo `driplytics` and tell me the organization or user name. Should CI run on **GitHub Actions** *(recommended)*?
- **Team:** will it be just you (plus AI agents) for Phase 0–1? This decides how strict code review and branch protection rules should be.
