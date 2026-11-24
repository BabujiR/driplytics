import { type NextRequest, NextResponse } from "next/server";

import { writeSession } from "@/lib/auth/cookies";
import { authConfig } from "@/lib/auth/config";
import { unseal } from "@/lib/auth/crypto";
import { exchangeCode } from "@/lib/auth/oidc";
import { LOGIN_COOKIE, type LoginState, cookieOptions } from "@/lib/auth/session";

export const dynamic = "force-dynamic";

function fail(req: NextRequest, message: string, status = 400) {
  const cfg = authConfig();
  const res = new NextResponse(
    `Sign-in failed: ${message}\n\nStart again: ${new URL("/auth/login", req.url).toString()}`,
    { status, headers: { "Content-Type": "text/plain; charset=utf-8" } },
  );
  res.cookies.set(LOGIN_COOKIE, "", cookieOptions(cfg.secureCookies, 0));
  return res;
}

/** The provider sends the browser back here with ?code&state. */
export async function GET(req: NextRequest) {
  const cfg = authConfig();
  const params = req.nextUrl.searchParams;
  const error = params.get("error");
  if (error) return fail(req, params.get("error_description") ?? error);

  const login = await unseal<LoginState>(req.cookies.get(LOGIN_COOKIE)?.value, cfg.sessionSecret);
  const code = params.get("code");
  if (!login || !code || params.get("state") !== login.state) {
    return fail(req, "the sign-in request expired or did not start here");
  }

  try {
    const session = await exchangeCode(cfg, code, login.verifier);
    const res = NextResponse.redirect(new URL(login.next, cfg.appUrl));
    await writeSession(res.cookies, session);
    res.cookies.set(LOGIN_COOKIE, "", cookieOptions(cfg.secureCookies, 0));
    return res;
  } catch (e) {
    console.error("token exchange failed:", e);
    return fail(req, "the identity provider did not accept the sign-in", 502);
  }
}
