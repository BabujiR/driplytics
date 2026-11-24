import { type NextRequest, NextResponse } from "next/server";

import { authConfig } from "@/lib/auth/config";
import { seal } from "@/lib/auth/crypto";
import { startLogin } from "@/lib/auth/oidc";
import { LOGIN_COOKIE, type LoginState, cookieOptions, safeNext } from "@/lib/auth/session";

export const dynamic = "force-dynamic";

/** Start sign-in: remember state + PKCE verifier (encrypted, 10 minutes) and go to the provider. */
export async function GET(req: NextRequest) {
  const cfg = authConfig();
  try {
    const { url, state, verifier } = await startLogin(cfg);
    const login: LoginState = { state, verifier, next: safeNext(req.nextUrl.searchParams.get("next")) };
    const res = NextResponse.redirect(url);
    res.cookies.set(LOGIN_COOKIE, await seal(login, cfg.sessionSecret), cookieOptions(cfg.secureCookies, 600));
    return res;
  } catch (e) {
    console.error("sign-in could not start:", e);
    return new NextResponse(
      "Sign-in is not available right now: the identity provider could not be reached. Try again in a minute.",
      { status: 503, headers: { "Content-Type": "text/plain; charset=utf-8", "Retry-After": "10" } },
    );
  }
}
