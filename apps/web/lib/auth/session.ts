/**
 * The browser session: tokens from the identity provider, encrypted into HTTP-only, SameSite=Lax
 * cookies (ADR 0004). Nothing is stored server-side. Browser JavaScript never sees a token: it calls
 * the API through the same-origin proxy (/api/v1/*), which adds the bearer token.
 */
import { seal, unseal } from "./crypto";

export interface Session {
  /** access token (sent to the API) */
  at: string;
  /** refresh token */
  rt?: string;
  /** access token expiry, epoch seconds */
  exp: number;
  /** refresh token expiry, epoch seconds (session end) */
  rexp: number;
}

export interface LoginState {
  state: string;
  verifier: string;
  next: string;
}

export const SESSION_COOKIE = "dl_session";
export const LOGIN_COOKIE = "dl_login";
export const TENANT_COOKIE = "dl_tenant";
export const SITE_COOKIE = "dl_site";

/** Browsers drop cookies over 4 KB, so a large session is split across dl_session.0, .1, ... */
const CHUNK = 3800;
const MAX_CHUNKS = 4;
/** Refresh when the access token has less than this many seconds left. */
const REFRESH_MARGIN_S = 60;

export interface CookieReader {
  get(name: string): { value: string } | undefined;
}

export interface CookieOptions {
  httpOnly: boolean;
  secure: boolean;
  sameSite: "lax";
  path: string;
  maxAge: number;
}

export function cookieOptions(secure: boolean, maxAge: number): CookieOptions {
  return { httpOnly: true, secure, sameSite: "lax", path: "/", maxAge };
}

/** The cookie name → value pairs to write for a sealed session (unused chunks are emptied). */
export function sessionChunks(sealed: string): Array<[string, string]> {
  const parts: string[] = [];
  for (let i = 0; i < sealed.length; i += CHUNK) parts.push(sealed.slice(i, i + CHUNK));
  if (parts.length > MAX_CHUNKS) throw new Error("session too large for cookies");
  return Array.from({ length: MAX_CHUNKS }, (_, i) => [`${SESSION_COOKIE}.${i}`, parts[i] ?? ""]);
}

export function readSealedSession(cookies: CookieReader): string | undefined {
  const parts: string[] = [];
  for (let i = 0; i < MAX_CHUNKS; i++) {
    const v = cookies.get(`${SESSION_COOKIE}.${i}`)?.value;
    if (!v) break;
    parts.push(v);
  }
  return parts.length ? parts.join("") : undefined;
}

export async function readSession(cookies: CookieReader, secret: string): Promise<Session | null> {
  const s = await unseal<Session>(readSealedSession(cookies), secret);
  if (!s || typeof s.at !== "string" || typeof s.exp !== "number") return null;
  if (s.rexp && s.rexp <= nowS()) return null;
  return s;
}

export function sealSession(session: Session, secret: string): Promise<string> {
  return seal(session, secret);
}

export function needsRefresh(session: Session, now = nowS()): boolean {
  return session.exp - REFRESH_MARGIN_S <= now;
}

/** Seconds the cookie should live: until the refresh token expires (at most 30 days). */
export function sessionMaxAge(session: Session, now = nowS()): number {
  return Math.max(0, Math.min(session.rexp - now, 30 * 86400));
}

export function nowS(): number {
  return Math.floor(Date.now() / 1000);
}

/** Only same-site paths are allowed after sign-in (no open redirects). */
export function safeNext(next: string | null | undefined): string {
  if (!next || !next.startsWith("/") || next.startsWith("//") || next.startsWith("/\\")) return "/";
  if (next.startsWith("/auth/")) return "/";
  return next;
}
