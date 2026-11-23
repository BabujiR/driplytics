/**
 * API contracts shared by the web app and the API (P0-13).
 * Types are generated from the FastAPI OpenAPI document; see client.ts and ADR 0020.
 */
import type { ReadinessResponse } from "./client";

export * from "./client";

export const API_BASE_PATH = "/api/v1";

export function isReady(r: ReadinessResponse): boolean {
  return r.status === "ok" && Object.values(r.checks).every((c) => c.ok);
}
