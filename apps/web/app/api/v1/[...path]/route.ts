/**
 * Same-origin proxy to the API (ADR 0021): the browser calls /api/v1/* with its session cookie;
 * this adds the bearer token and the selected organization (X-Tenant-Id) and forwards to the API.
 * Tokens never reach browser JavaScript. Middleware has already refreshed the session if needed.
 */
import { cookies } from "next/headers";
import { type NextRequest, NextResponse } from "next/server";

import { apiInternalUrl, authConfig } from "@/lib/auth/config";
import { TENANT_COOKIE, readSession } from "@/lib/auth/session";

export const dynamic = "force-dynamic";

const PASS_REQUEST = ["accept", "content-type", "x-tenant-id", "x-request-id"];
const PASS_RESPONSE = ["content-type", "content-disposition", "cache-control", "location", "retry-after", "x-request-id"];
const UNSAFE = new Set(["POST", "PUT", "PATCH", "DELETE"]);

/** Cookie-authenticated writes must come from our own pages (CSRF), on top of SameSite=Lax. */
function crossSite(req: NextRequest): boolean {
  if (!UNSAFE.has(req.method)) return false;
  const origin = req.headers.get("origin");
  if (origin) return new URL(origin).host !== req.headers.get("host");
  return req.headers.get("sec-fetch-site") === "cross-site";
}

async function proxy(req: NextRequest, ctx: { params: Promise<{ path: string[] }> }) {
  if (crossSite(req)) return NextResponse.json({ detail: "cross-site request refused" }, { status: 403 });

  const store = await cookies();
  const session = await readSession(store, authConfig().sessionSecret);
  if (!session) return NextResponse.json({ detail: "not signed in" }, { status: 401 });

  const { path } = await ctx.params;
  const target = `${apiInternalUrl()}/api/v1/${path.map(encodeURIComponent).join("/")}${req.nextUrl.search}`;

  const headers = new Headers();
  for (const h of PASS_REQUEST) {
    const v = req.headers.get(h);
    if (v) headers.set(h, v);
  }
  headers.set("authorization", `Bearer ${session.at}`);
  // The selected organization: the dl_tenant cookie, or (first visit, nothing chosen yet) the user's
  // first organization, the same default the pages use. Remembered in the cookie below.
  let tenant = store.get(TENANT_COOKIE)?.value;
  let rememberTenant = false;
  if (!tenant && !headers.has("x-tenant-id")) {
    tenant = await firstTenant(session.at);
    rememberTenant = Boolean(tenant);
  }
  if (tenant && !headers.has("x-tenant-id")) headers.set("x-tenant-id", tenant);

  let upstream: Response;
  try {
    upstream = await fetch(target, {
      method: req.method,
      headers,
      body: req.method === "GET" || req.method === "HEAD" ? undefined : await req.arrayBuffer(),
      cache: "no-store",
      redirect: "manual",
    });
  } catch {
    return NextResponse.json({ detail: "the API is not reachable" }, { status: 502 });
  }

  const out = new Headers();
  for (const h of PASS_RESPONSE) {
    const v = upstream.headers.get(h);
    if (v) out.set(h, v);
  }
  const res = new NextResponse(upstream.status === 204 ? null : upstream.body, { status: upstream.status, headers: out });
  if (rememberTenant && tenant) res.cookies.set(TENANT_COOKIE, tenant, { path: "/", sameSite: "lax", maxAge: 31536000 });
  return res;
}

async function firstTenant(accessToken: string): Promise<string | undefined> {
  try {
    const r = await fetch(`${apiInternalUrl()}/api/v1/me`, {
      headers: { authorization: `Bearer ${accessToken}` },
      cache: "no-store",
    });
    if (!r.ok) return undefined;
    const me = (await r.json()) as { memberships?: Array<{ tenant_id: string }> };
    return me.memberships?.[0]?.tenant_id;
  } catch {
    return undefined;
  }
}

export { proxy as DELETE, proxy as GET, proxy as PATCH, proxy as POST, proxy as PUT };
