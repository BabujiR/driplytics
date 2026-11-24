import { describe, expect, it } from "vitest";

import { detectDelimiter, isParquet, previewCsv, splitCsvLine } from "./detect";

describe("previewCsv", () => {
  it("detects a long export", () => {
    const p = previewCsv(
      "﻿timestamp,tag,value,quality\n2026-03-08 01:50:00,FIT-101.PV,240.3,Good\n2026-03-08 01:50:00,P-201.RUN,RUNNING,Good\n",
    );
    expect(p.format).toBe("long");
    expect(p.header).toEqual(["timestamp", "tag", "value", "quality"]);
    expect(p.tags).toEqual(["FIT-101.PV", "P-201.RUN"]);
    expect(p.warnings).toEqual([]);
  });

  it("detects a wide export and skips quality columns", () => {
    const p = previewCsv("timestamp,FIT-101.PV,FIT-101.PV Quality,PIT-101.PV\n2026-11-01 00:50:00,252.8,Good,55.5\n");
    expect(p.format).toBe("wide");
    expect(p.tags).toEqual(["FIT-101.PV", "PIT-101.PV"]);
  });

  it("finds semicolons and warns about an unexpected time column", () => {
    const p = previewCsv("Time;TagName;Val\n01.11.2026 00:50;FIT-101.PV;252,8\n");
    expect(p.delimiter).toBe(";");
    expect(p.warnings.join(" ")).toContain('called "Time"');
    expect(p.warnings.join(" ")).toContain("looks like a long export");
  });

  it("drops a cut-off last line when only the start of a big file was read", () => {
    const body = "timestamp,tag,value\n" + "2026-01-01 00:00:00,A,1\n".repeat(3000);
    const p = previewCsv(body.slice(0, 64 * 1024));
    expect(p.rows.every((r) => r.length === 3)).toBe(true);
  });

  it("handles an empty file", () => {
    expect(previewCsv("").warnings).toEqual(["The file is empty."]);
  });
});

describe("helpers", () => {
  it("splits quoted CSV", () => {
    expect(splitCsvLine('a,"b,c","say ""hi"""', ",")).toEqual(["a", "b,c", 'say "hi"']);
  });
  it("detects delimiters and Parquet", () => {
    expect(detectDelimiter("a\tb\tc")).toBe("\t");
    expect(isParquet("x.PARQUET")).toBe(true);
    expect(isParquet("x.csv")).toBe(false);
  });
});
