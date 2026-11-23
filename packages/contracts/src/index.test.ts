import { describe, expect, it } from "vitest";

import { isReady, type ReadinessResponse } from "./index";

describe("isReady", () => {
  it("is true only when every check passes", () => {
    const ok: ReadinessResponse = { status: "ok", checks: { postgres: { ok: true, detail: "" } } };
    const bad: ReadinessResponse = { status: "degraded", checks: { redis: { ok: false, detail: "refused" } } };
    expect(isReady(ok)).toBe(true);
    expect(isReady(bad)).toBe(false);
  });
});
