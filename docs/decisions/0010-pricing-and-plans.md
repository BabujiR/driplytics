# 0010. Pricing and plans

- **Status:** Accepted
- **Date:** 2026-11-22
- **Answers:** Q5 in `docs/questions.md`

## Decision
| Plan | Mapped tags per site | Price |
|---|---|---|
| Pilot | up to 2,000 | $5,000–15,000 one-time, 30 days, **fully creditable** toward the first year if they subscribe within 60 days |
| Starter | 500 | $1,000 / site / month, billed annually |
| Professional | 2,000 | $2,500 / site / month, billed annually |
| Enterprise | 10,000+ | from $5,000 / site / month, custom |

- **Only mapped tags count.** Unmapped and ignored tags are free.
- **Savings-share pricing is not self-serve at launch.** Quote it case by case once the verified savings ledger exists (Phase 2).
- The product enforces tag limits with a soft warning at 90% and a hard stop above 110%, and shows usage in Settings.
- Billing through Stripe; annual invoices with purchase-order numbers supported for utilities.

## Consequences
Plan limits and usage metering are needed in Phase 3. Prices are configuration, not code, so they can change without a release.
