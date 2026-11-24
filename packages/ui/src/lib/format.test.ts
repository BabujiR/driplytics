import { describe, expect, it } from "vitest";

import {
  formatBytes,
  formatCount,
  formatDateTime,
  formatDollarRange,
  formatDollars,
  formatPercent,
  formatQuantity,
  formatRelative,
  initials,
} from "./format";

describe("format", () => {
  it("counts with thousands separators", () => {
    expect(formatCount(5179)).toBe("5,179");
  });

  it("rounds dollars sensibly", () => {
    expect(formatDollars(84200, "yr")).toBe("$84.2k/yr");
    expect(formatDollars(950)).toBe("$950");
    expect(formatDollars(999.6)).toBe("$1k");
    expect(formatDollars(31500)).toBe("$31.5k");
    expect(formatDollars(250_000)).toBe("$250k");
    expect(formatDollars(1_250_000)).toBe("$1.25M");
    expect(formatDollars(-2500)).toBe("-$2.5k");
    expect(formatDollarRange(6000, 9000, "yr")).toBe("$6k–$9k/yr");
  });

  it("percent, bytes and quantities always carry units", () => {
    expect(formatPercent(0.4567)).toBe("45.7 %");
    expect(formatBytes(222428)).toBe("217 KB");
    expect(formatBytes(15 * 1024 ** 3)).toBe("15 GB");
    expect(formatQuantity(3.956, "gpm")).toBe("3.96 gpm");
  });

  it("shows times in the site's zone with the zone label (DST fall-back hour is unambiguous)", () => {
    expect(formatDateTime("2026-11-01T05:30:00Z", "America/New_York")).toBe("Nov 1, 2026, 1:30 AM EDT");
    expect(formatDateTime("2026-11-01T06:30:00Z", "America/New_York")).toBe("Nov 1, 2026, 1:30 AM EST");
  });

  it("relative times and initials", () => {
    const now = new Date("2026-11-23T12:00:00Z");
    expect(formatRelative("2026-11-23T10:00:00Z", now)).toBe("2 h ago");
    expect(formatRelative("2026-11-23T11:59:50Z", now)).toBe("just now");
    expect(initials("Alice Riverbend")).toBe("AR");
    expect(initials("bob@lakeside.test")).toBe("BO");
  });
});
