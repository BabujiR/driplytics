import { describe, expect, it } from "vitest";

import { brand, cx } from "./index";

describe("@driplytics/ui", () => {
  it("exposes the brand name", () => {
    expect(brand.name).toBe("Driplytics");
  });

  it("cx joins truthy class names", () => {
    expect(cx("a", false, null, undefined, "b")).toBe("a b");
  });
});
