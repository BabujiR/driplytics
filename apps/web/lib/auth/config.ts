/**
 * Sign-in settings (ADR 0004, ADR 0021). Read lazily so `next build` needs no secrets.
 *
 *   OIDC_DISCOVERY_URL  where the web server reads the provider's endpoints. In Docker this is the
 *                       internal address (http://keycloak:8080/...); Keycloak still hands the browser
 *                       public URLs (KC_HOSTNAME) and the server back-channel ones.
 *   OIDC_CLIENT_ID / OIDC_CLIENT_SECRET   the confidential web client
 *   APP_URL             public origin of the web app, for the redirect URI
 *   SESSION_SECRET      32+ characters; encrypts the session cookie
 *   API_INTERNAL_URL    where the web server reaches the API
 */

export interface AuthConfig {
  discoveryUrl: string;
  clientId: string;
  clientSecret: string;
  appUrl: string;
  sessionSecret: string;
  secureCookies: boolean;
}

// Local development defaults only; production must set every value.
const DEV = {
  discoveryUrl: "http://localhost:8080/realms/driplytics/.well-known/openid-configuration",
  clientId: "driplytics-web",
  clientSecret: "driplytics-web-dev-secret",
  sessionSecret: "dev-only-session-secret-change-me-0123456789",
};

function env(name: string, devDefault?: string): string {
  const v = process.env[name];
  if (v) return v;
  if (process.env.NODE_ENV !== "production" && devDefault !== undefined) return devDefault;
  throw new Error(`${name} is not set`);
}

export function authConfig(): AuthConfig {
  const appUrl = env("APP_URL", "http://localhost:3000").replace(/\/+$/, "");
  const sessionSecret = env("SESSION_SECRET", DEV.sessionSecret);
  if (sessionSecret.length < 32) throw new Error("SESSION_SECRET must be at least 32 characters");
  return {
    discoveryUrl: env("OIDC_DISCOVERY_URL", DEV.discoveryUrl),
    clientId: env("OIDC_CLIENT_ID", DEV.clientId),
    clientSecret: env("OIDC_CLIENT_SECRET", DEV.clientSecret),
    appUrl,
    sessionSecret,
    secureCookies: appUrl.startsWith("https://"),
  };
}

export function apiInternalUrl(): string {
  return env("API_INTERNAL_URL", "http://localhost:8000").replace(/\/+$/, "");
}
