/**
 * Typed client for the Driplytics API (P0-13, ADR 0020).
 *
 * Request and response types come from `generated/openapi.ts`, which is generated from the API's
 * OpenAPI document, so a call that doesn't match the API fails `tsc`, not the browser.
 *
 *   const api = createApiClient({ baseUrl: "http://localhost:8000", getToken, getTenantId });
 *   const sites = await unwrap(api.GET("/api/v1/sites"));
 *   const site = await unwrap(api.GET("/api/v1/sites/{site_id}", { params: { path: { site_id } } }));
 */
import createClient, { type Client, type Middleware } from "openapi-fetch";

import type { components, paths } from "./generated/openapi";

export type { components, paths };
export type Schemas = components["schemas"];

// Names the screens use. They are aliases, so they always match the generated contract.
export type Me = Schemas["MeOut"];
export type Membership = Schemas["MembershipOut"];
export type CurrentTenant = Schemas["CurrentTenantOut"];
export type Site = Schemas["SiteOut"];
export type SiteCreate = Schemas["SiteCreate"];
export type SiteUpdate = Schemas["SiteUpdate"];
export type ExportProfile = Schemas["ExportProfileOut"];
export type ExportLayout = Schemas["ExportLayoutModel"];
export type TagMapping = Schemas["TagMappingOut"];
export type Import = Schemas["ImportOut"];
export type ImportDetail = Schemas["ImportDetailOut"];
export type ImportCreated = Schemas["ImportCreatedOut"];
export type ImportReport = Schemas["ImportReportOut"];
export type ImportStatus = Import["status"];
export type UploadTarget = Schemas["UploadTarget"];
export type AuditEvent = Schemas["AuditEventOut"];
export type ReadinessResponse = Schemas["ReadinessOut"];
export type DependencyCheck = Schemas["DependencyCheck"];
export type VersionResponse = Schemas["VersionOut"];

export type ApiClient = Client<paths>;

type Maybe<T> = T | null | undefined;

export interface ApiClientOptions {
  /** Origin of the API, e.g. http://localhost:8000. Paths already start with /api/v1. */
  baseUrl: string;
  /** Current access token (called before every request). */
  getToken?: () => Maybe<string> | Promise<Maybe<string>>;
  /** Selected organization; sent as X-Tenant-Id (called before every request). */
  getTenantId?: () => Maybe<string>;
  /** Swap the fetch implementation (tests, server components). */
  fetch?: typeof globalThis.fetch;
}

export function createApiClient(options: ApiClientOptions): ApiClient {
  const client = createClient<paths>({
    baseUrl: options.baseUrl.replace(/\/+$/, ""),
    ...(options.fetch ? { fetch: options.fetch } : {}),
  });
  const auth: Middleware = {
    async onRequest({ request }) {
      const token = await options.getToken?.();
      if (token) request.headers.set("Authorization", `Bearer ${token}`);
      const tenantId = options.getTenantId?.();
      if (tenantId) request.headers.set("X-Tenant-Id", tenantId);
      return request;
    },
  };
  client.use(auth);
  return client;
}

/** A non-2xx answer from the API, with a message that is safe to show in the UI. */
export class ApiError extends Error {
  readonly status: number;
  readonly body: unknown;

  constructor(status: number, body: unknown) {
    super(errorMessage(status, body));
    this.name = "ApiError";
    this.status = status;
    this.body = body;
  }
}

interface ValidationIssue {
  loc?: (string | number)[];
  msg?: string;
}

/** FastAPI sends {detail: "text"} for our errors and {detail: [{loc, msg}]} for invalid input. */
export function errorMessage(status: number, body: unknown): string {
  const detail = (body as { detail?: unknown } | null)?.detail;
  if (typeof detail === "string" && detail) return detail;
  if (Array.isArray(detail) && detail.length) {
    return (detail as ValidationIssue[])
      .map((d) => {
        const field = (d.loc ?? []).filter((p) => p !== "body").join(".");
        return field ? `${field}: ${d.msg ?? "invalid"}` : (d.msg ?? "invalid");
      })
      .join("; ");
  }
  return `request failed (HTTP ${status})`;
}

interface Result<T> {
  data?: T;
  error?: unknown;
  response: Response;
}

/** Await an openapi-fetch call and return its data, or throw ApiError. */
export async function unwrap<T>(call: Promise<Result<T>>): Promise<T> {
  const { data, error, response } = await call;
  if (!response.ok || error !== undefined) throw new ApiError(response.status, error);
  return data as T;
}

/**
 * Send a file to the presigned URL from `POST /sites/{site_id}/imports`. The file goes straight to
 * object storage; it never passes through the API. (The upload screen uses XMLHttpRequest instead
 * when it needs a progress bar.)
 */
export async function uploadToTarget(
  target: UploadTarget,
  file: Blob,
  fetchImpl: typeof globalThis.fetch = globalThis.fetch,
): Promise<void> {
  const res = await fetchImpl(target.url, { method: target.method, headers: target.headers, body: file });
  if (!res.ok) throw new ApiError(res.status, { detail: `upload to storage failed (HTTP ${res.status})` });
}

const FINISHED: readonly ImportStatus[] = ["succeeded", "failed", "cancelled"];

/** True once the worker is done with the import, successfully or not. */
export function isFinished(status: ImportStatus): boolean {
  return FINISHED.includes(status);
}
