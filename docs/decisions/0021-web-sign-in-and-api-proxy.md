# 0021. Web sign-in: server-side OIDC code flow, encrypted cookie session, same-origin API proxy

- **Status:** Accepted
- **Date:** 2026-11-23

## Context
ADR 0004 calls for short-lived access tokens and HTTP-only, secure, SameSite cookies for the web app.
The browser must never hold tokens (XSS can't steal what JavaScript can't read), the same code must work
with Keycloak (local, on-prem) and WorkOS (cloud), and the Docker setup has two addresses for Keycloak
(the browser's `localhost:8080`, the server's `keycloak:8080`).

## Decision
- **Authorization code flow with PKCE (S256)**, run by Next.js route handlers (`/auth/login`,
  `/auth/callback`, `/auth/logout`) with the confidential `driplytics-web` client. Endpoints come from
  OIDC discovery (`OIDC_DISCOVERY_URL`); Keycloak returns browser-facing URLs for redirects and
  back-channel URLs for the token endpoint (`KC_HOSTNAME_BACKCHANNEL_DYNAMIC`).
- **Session = encrypted cookie**, no server-side store: access + refresh token sealed with AES-256-GCM
  (key from `SESSION_SECRET`), HTTP-only, SameSite=Lax, Secure on https, split into ≤3.8 KB chunks.
  Written with Web Crypto only, so it runs in Edge middleware and Node alike; no auth library.
- **Middleware** guards every page and `/api/v1/*`: no session → sign-in (pages) or 401 (API); access token
  within 60 s of expiry → refreshed, written back, and forwarded to the same request.
- **Same-origin proxy** `/api/v1/*` → the API with `Authorization: Bearer` and `X-Tenant-Id` (from the
  `dl_tenant` cookie). Writes are refused unless they come from our own origin (CSRF, on top of SameSite).
  Server components call the API directly with the session's token.
- The web app never trusts ID-token claims: the API verifies every access token (JWKS) and owns roles.
- Selected organization and site live in plain cookies (`dl_tenant`, `dl_site`); they are preferences,
  not authority: row-level security and role checks in the API decide access.

## Consequences
- Switching to WorkOS is configuration (discovery URL, client ID, secret).
- Big file uploads still go straight to object storage with presigned URLs (ADR 0019), never through
  the proxy. Logout without an ID token shows Keycloak's "log out?" confirmation; acceptable for Phase 0.
- Alternatives considered: Auth.js (discovery inside Docker needs workarounds; more moving parts than
  ~250 lines we can read and test), tokens in browser storage (rejected: XSS exposure).
