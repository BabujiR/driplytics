# 0013. Data retention

- **Status:** Accepted
- **Date:** 2026-11-22
- **Answers:** Q8 in `docs/questions.md`

## Decision
| Data | Default retention |
|---|---|
| Raw uploaded files and connector batches | 2 years |
| Clean time series (Parquet) | 5 years |
| Findings, verifications, savings ledger, audit log | Life of the account (needed to prove savings) |
| Data of a tenant who leaves | Exported on request, then purged within 30 days |

Customers can shorten retention by contract. Enforced with object-storage lifecycle rules plus a nightly purge job that writes to the audit log.
