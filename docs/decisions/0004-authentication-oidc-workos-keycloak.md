# 0004. Authentication: OIDC, with WorkOS in the cloud and Keycloak locally and on-prem

- **Status:** Accepted
- **Date:** 2026-11-22
- **Answers:** Q3 in `docs/questions.md`

## Decision
- The API depends only on **standard OIDC** (an issuer URL, client ID and secret, and JWKS validation) behind an `IdentityProvider` interface.
- **Cloud (GCP now, AWS later):** WorkOS, for email/password with MFA, SAML/OIDC enterprise SSO (Entra ID, Okta, Google) and directory sync when needed.
- **Local development and on-prem (mode C):** Keycloak in a container.
- Roles live in **our** database (`membership.role`: Owner, Admin, Engineer, Technician, Viewer, Partner), not in the identity provider, so authorization works the same everywhere.
- Sessions: short-lived access tokens plus HTTP-only, secure, SameSite cookies for the web app.

## Consequences
Enterprise SSO for utilities becomes configuration rather than a project. Switching vendors is a configuration change. Two identity setups to test, which CI covers with Keycloak.
