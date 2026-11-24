"use client";

/** Calling the API from client components: same-origin /api/v1/* through the proxy (cookies). */
import { type ApiClient, createApiClient } from "@driplytics/contracts";

let client: ApiClient | null = null;

export function browserApi(): ApiClient {
  client ??= createApiClient({ baseUrl: window.location.origin });
  return client;
}

/** Remember a selection for a year (read by server components and the proxy). */
export function setSelectionCookie(name: "dl_tenant" | "dl_site", value: string | null): void {
  const attrs = "path=/; samesite=lax";
  document.cookie = value ? `${name}=${encodeURIComponent(value)}; max-age=31536000; ${attrs}` : `${name}=; max-age=0; ${attrs}`;
}
