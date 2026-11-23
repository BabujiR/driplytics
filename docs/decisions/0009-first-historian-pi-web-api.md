# 0009. First historian integration: AVEVA PI via PI Web API

- **Status:** Accepted
- **Date:** 2026-11-22
- **Answers:** Q4 in `docs/questions.md`

## Decision
- **File imports (Phase 1):** ship export profiles for PI (long and wide, including PI DataLink-style wide exports) first; IP.21 profiles next.
- **Edge connector (Phase 3):** first source is **PI Web API** (recorded and interpolated values, Kerberos/NTLM/Basic auth). **OPC UA** is the second source. IP.21 is added when a paying customer needs it.
- Build a PI Web API mock server (Docker) with synthetic tags for tests and demos.

## Override
If the first committed pilot customer runs a different historian, their historian moves to the front.
