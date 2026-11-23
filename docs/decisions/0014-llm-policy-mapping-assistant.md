# 0014. LLM provider and data policy for the mapping assistant

- **Status:** Accepted
- **Date:** 2026-11-22
- **Answers:** Q9 in `docs/questions.md`

## Decision
- **Provider:** Anthropic Claude via API, behind an `LLMProvider` interface so it can be swapped, pointed at a customer-hosted model, or disabled.
- **What may be sent:** tag names, descriptions, engineering units, and summary statistics (min/max/mean, distinct-value counts, monotonic yes/no). **Never raw time series, never customer names or locations.**
- **Defaults:** a per-tenant switch, **on** for cloud tenants (disclosed in the terms and the in-app mapping screen), **off** for on-prem (mode C).
- The mapping assistant must work fully without an LLM (naming rules + behavioral detection). The LLM only improves suggestions.
- Every LLM suggestion is stored with its confidence and rationale, and needs human confirmation before it is used for scoring.
