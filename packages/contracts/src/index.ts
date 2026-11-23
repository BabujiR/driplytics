/**
 * API contracts shared by the web app and the API.
 * Phase 0: hand-written types for the health endpoints. P0-13 replaces this with a client
 * generated from the FastAPI OpenAPI spec (/api/openapi.json).
 */

export const API_BASE_PATH = "/api/v1";

export interface DependencyCheck {
  ok: boolean;
  detail: string;
}

export interface ReadinessResponse {
  status: "ok" | "degraded";
  checks: Record<string, DependencyCheck>;
}

export interface VersionResponse {
  service: string;
  version: string;
  env: string;
}

export function isReady(r: ReadinessResponse): boolean {
  return r.status === "ok" && Object.values(r.checks).every((c) => c.ok);
}
