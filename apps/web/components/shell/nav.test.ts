import { describe, expect, it } from "vitest";

import { NAV, isActive } from "./nav";

describe("navigation", () => {
  it("highlights the right item", () => {
    expect(isActive("/", "/")).toBe(true);
    expect(isActive("/", "/data/imports")).toBe(false);
    expect(isActive("/data/imports", "/data/imports/123")).toBe(true);
    expect(isActive("/data/imports", "/data/imports-old")).toBe(false);
  });

  it("follows the information architecture (CLAUDE.md §12.3)", () => {
    expect(NAV.flatMap((g) => g.items.map((i) => i.label))).toEqual([
      "Worklist",
      "Findings",
      "Assets",
      "Imports",
      "Tag mapping",
      "Connectors",
      "Field kit",
      "Savings",
      "Reports",
      "Settings",
    ]);
  });
});
