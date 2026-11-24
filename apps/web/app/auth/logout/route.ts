import { type NextRequest, NextResponse } from "next/server";

import { clearSession } from "@/lib/auth/cookies";
import { authConfig } from "@/lib/auth/config";
import { logoutUrl } from "@/lib/auth/oidc";
import { SITE_COOKIE, TENANT_COOKIE } from "@/lib/auth/session";

export const dynamic = "force-dynamic";

/** Sign out (POST from the user menu, so a link elsewhere can't sign you out). */
export async function POST(req: NextRequest) {
  const cfg = authConfig();
  const origin = req.headers.get("origin");
  if (origin && new URL(origin).host !== req.headers.get("host")) {
    return new NextResponse("cross-site sign-out refused", { status: 403 });
  }
  const res = NextResponse.redirect((await logoutUrl(cfg)) ?? new URL("/", cfg.appUrl), { status: 303 });
  clearSession(res.cookies);
  res.cookies.delete(TENANT_COOKIE);
  res.cookies.delete(SITE_COOKIE);
  return res;
}
