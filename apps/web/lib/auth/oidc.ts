/**
 * Authorization code flow with PKCE against any standard OIDC provider (Keycloak locally,
 * WorkOS in the cloud: ADR 0004). Runs in Edge and Node. The web app never validates ID tokens:
 * it only forwards the access token, and the API verifies its signature (JWKS) on every call.
 */
import type { AuthConfig } from "./config";
import { pkceChallenge, randomToken } from "./crypto";
import { type Session, nowS } from "./session";

interface Discovery {
  authorization_endpoint: string;
  token_endpoint: string;
  end_session_endpoint?: string;
}

let discovery: Promise<Discovery> | null = null;

export function discover(cfg: AuthConfig): Promise<Discovery> {
  if (!discovery) {
    discovery = fetch(cfg.discoveryUrl, { cache: "no-store" })
      .then(async (r) => {
        if (!r.ok) throw new Error(`OIDC discovery failed: HTTP ${r.status} from ${cfg.discoveryUrl}`);
        return (await r.json()) as Discovery;
      })
      .catch((e: unknown) => {
        discovery = null; // retry on the next request (the provider may still be starting)
        throw e;
      });
  }
  return discovery;
}

export function redirectUri(cfg: AuthConfig): string {
  return `${cfg.appUrl}/auth/callback`;
}

export async function startLogin(cfg: AuthConfig): Promise<{ url: string; state: string; verifier: string }> {
  const d = await discover(cfg);
  const state = randomToken(24);
  const verifier = randomToken(48);
  const url = new URL(d.authorization_endpoint);
  url.search = new URLSearchParams({
    response_type: "code",
    client_id: cfg.clientId,
    redirect_uri: redirectUri(cfg),
    scope: "openid email profile",
    state,
    code_challenge: await pkceChallenge(verifier),
    code_challenge_method: "S256",
  }).toString();
  return { url: url.toString(), state, verifier };
}

interface TokenResponse {
  access_token: string;
  refresh_token?: string;
  expires_in: number;
  refresh_expires_in?: number;
}

export class TokenError extends Error {}

async function tokenRequest(cfg: AuthConfig, params: Record<string, string>): Promise<Session> {
  const d = await discover(cfg);
  const basic = btoa(`${encodeURIComponent(cfg.clientId)}:${encodeURIComponent(cfg.clientSecret)}`);
  const res = await fetch(d.token_endpoint, {
    method: "POST",
    cache: "no-store",
    headers: { "Content-Type": "application/x-www-form-urlencoded", Authorization: `Basic ${basic}` },
    body: new URLSearchParams(params).toString(),
  });
  if (!res.ok) throw new TokenError(`token endpoint answered HTTP ${res.status}: ${await res.text()}`);
  return toSession((await res.json()) as TokenResponse);
}

export function toSession(t: TokenResponse, now = nowS()): Session {
  return {
    at: t.access_token,
    ...(t.refresh_token ? { rt: t.refresh_token } : {}),
    exp: now + t.expires_in,
    // Keycloak sends refresh_expires_in; 0 means "offline" (no fixed end). Default: 8 hours.
    rexp: now + (t.refresh_expires_in && t.refresh_expires_in > 0 ? t.refresh_expires_in : 8 * 3600),
  };
}

export function exchangeCode(cfg: AuthConfig, code: string, verifier: string): Promise<Session> {
  return tokenRequest(cfg, {
    grant_type: "authorization_code",
    code,
    redirect_uri: redirectUri(cfg),
    code_verifier: verifier,
  });
}

export async function refreshSession(cfg: AuthConfig, session: Session): Promise<Session> {
  if (!session.rt) throw new TokenError("no refresh token");
  const fresh = await tokenRequest(cfg, { grant_type: "refresh_token", refresh_token: session.rt });
  return { ...fresh, rt: fresh.rt ?? session.rt };
}

/** Where to send the browser to end the provider session too (null if the provider has none). */
export async function logoutUrl(cfg: AuthConfig): Promise<string | null> {
  const d = await discover(cfg).catch(() => null);
  if (!d?.end_session_endpoint) return null;
  const url = new URL(d.end_session_endpoint);
  url.search = new URLSearchParams({ client_id: cfg.clientId, post_logout_redirect_uri: `${cfg.appUrl}/` }).toString();
  return url.toString();
}
