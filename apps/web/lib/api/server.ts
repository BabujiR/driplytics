/** Calling the API from server components (pages, layouts). */
import { ApiError, type ApiClient, createApiClient, unwrap } from "@driplytics/contracts";
import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { cache } from "react";

import { apiInternalUrl, authConfig } from "../auth/config";
import { SITE_COOKIE, TENANT_COOKIE, readSession } from "../auth/session";

/** An API client acting as the signed-in user, optionally for one organization. */
export async function serverApi(tenantId?: string): Promise<ApiClient> {
  const session = await readSession(await cookies(), authConfig().sessionSecret);
  if (!session) redirect("/auth/login");
  return createApiClient({
    baseUrl: apiInternalUrl(),
    getToken: () => session.at,
    getTenantId: () => tenantId,
    fetch: (input) => fetch(input, { cache: "no-store" }),
  });
}

/** unwrap(), but an expired or rejected sign-in goes back to the sign-in page. */
export async function load<T>(call: Promise<{ data?: T; error?: unknown; response: Response }>): Promise<T> {
  try {
    return await unwrap(call);
  } catch (e) {
    if (e instanceof ApiError && e.status === 401) redirect("/auth/login");
    throw e;
  }
}

/**
 * Who is signed in, which organization and site are selected. Cached per request, so the layout
 * and the page share one set of API calls. Selections live in cookies (dl_tenant, dl_site).
 */
export const getAppContext = cache(async () => {
  const store = await cookies();
  const me = await load((await serverApi()).GET("/api/v1/me"));
  const wanted = store.get(TENANT_COOKIE)?.value;
  const membership = me.memberships.find((m) => m.tenant_id === wanted) ?? me.memberships[0];
  if (!membership) return { me, membership: null, tenant: null, site: null, api: null } as const;

  const api = await serverApi(membership.tenant_id);
  const tenant = await load(api.GET("/api/v1/tenants/current"));
  const wantedSite = store.get(SITE_COOKIE)?.value;
  const site = tenant.sites.find((s) => s.id === wantedSite) ?? tenant.sites[0] ?? null;
  return { me, membership, tenant, site, api } as const;
});

export type AppContext = Awaited<ReturnType<typeof getAppContext>>;
