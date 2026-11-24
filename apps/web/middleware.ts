/**
 * Every app page and /api/v1 call needs a session (ADR 0021). This keeps the access token fresh:
 * when it is about to expire, it is refreshed here, written back to the browser, and forwarded to
 * the page or proxy handling this same request.
 */
import { type NextRequest, NextResponse } from "next/server";

import { clearSession, writeSession } from "./lib/auth/cookies";
import { authConfig } from "./lib/auth/config";
import { refreshSession } from "./lib/auth/oidc";
import { needsRefresh, readSession } from "./lib/auth/session";

export const config = {
  // Everything except sign-in routes, Next internals, health/status and static files.
  matcher: ["/((?!auth/|_next/|api/health|status|favicon\\.ico|.*\\.(?:svg|png|jpg|ico|webp|woff2?)$).*)"],
};

function signedOut(req: NextRequest): NextResponse {
  if (req.nextUrl.pathname.startsWith("/api/")) {
    return NextResponse.json({ detail: "not signed in" }, { status: 401 });
  }
  const login = new URL("/auth/login", req.url);
  login.searchParams.set("next", req.nextUrl.pathname + req.nextUrl.search);
  return NextResponse.redirect(login);
}

export async function middleware(req: NextRequest): Promise<NextResponse> {
  const cfg = authConfig();
  const session = await readSession(req.cookies, cfg.sessionSecret);
  if (!session) return signedOut(req);
  if (!needsRefresh(session)) return NextResponse.next();

  try {
    const fresh = await refreshSession(cfg, session);
    // Write the new cookies on the response, then copy them into this request's Cookie header.
    const res = NextResponse.next();
    const chunks = await writeSession(res.cookies, fresh);
    for (const [name, value] of chunks) {
      if (value) req.cookies.set(name, value);
      else req.cookies.delete(name);
    }
    const forwarded = NextResponse.next({ request: { headers: req.headers } });
    res.cookies.getAll().forEach((c) => forwarded.cookies.set(c));
    return forwarded;
  } catch {
    const res = signedOut(req);
    clearSession(res.cookies);
    return res;
  }
}
