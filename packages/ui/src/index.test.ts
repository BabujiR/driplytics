import { describe, expect, it } from "vitest";

import { brand, cn } from "./index";

describe("@driplytics/ui", () => {
  it("exposes the brand", () => {
    expect(brand.name).toBe("Driplytics");
  });

  it("cn merges Tailwind classes, later ones win", () => {
    expect(cn("px-2 text-sm", false, null, "px-4")).toBe("text-sm px-4");
    expect(cn("text-fg", "text-sm")).toBe("text-fg text-sm"); // a token color and a size don't clash
    expect(cn("bg-surface", "bg-surface-2")).toBe("bg-surface-2");
  });
});
