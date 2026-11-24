/**
 * Look at the first bytes of a historian export in the browser, before uploading it: delimiter,
 * long vs wide format and a preview of the first rows (CLAUDE.md §12.4, onboarding step 1).
 * Mirrors the engine's default layout (driplytics_engine.readers): "long" when the header has
 * `tag` and `value` columns, otherwise "wide" (one column per tag); timestamps in `timestamp`.
 */

export type ExportFormat = "long" | "wide";

export interface Preview {
  kind: "csv";
  delimiter: string;
  format: ExportFormat;
  header: string[];
  rows: string[][];
  /** Distinct tags seen in the preview (long) or tag columns (wide). */
  tags: string[];
  /** Things to check before importing, in plain words. */
  warnings: string[];
}

export interface ParquetPreview {
  kind: "parquet";
  warnings: string[];
}

export const PREVIEW_BYTES = 64 * 1024;
const PREVIEW_ROWS = 6;
const DELIMITERS = [",", ";", "\t", "|"];

export function isParquet(name: string): boolean {
  return /\.(parquet|pq)$/i.test(name);
}

/** Split one CSV line, honoring double quotes ("a,b" and "" escapes). */
export function splitCsvLine(line: string, delimiter: string): string[] {
  const out: string[] = [];
  let cur = "";
  let quoted = false;
  for (let i = 0; i < line.length; i++) {
    const c = line[i];
    if (quoted) {
      if (c === '"' && line[i + 1] === '"') {
        cur += '"';
        i++;
      } else if (c === '"') quoted = false;
      else cur += c;
    } else if (c === '"') quoted = true;
    else if (c === delimiter) {
      out.push(cur.trim());
      cur = "";
    } else cur += c;
  }
  out.push(cur.trim());
  return out;
}

export function detectDelimiter(headerLine: string): string {
  let best = ",";
  let bestCount = 0;
  for (const d of DELIMITERS) {
    const n = splitCsvLine(headerLine, d).length - 1;
    if (n > bestCount) {
      best = d;
      bestCount = n;
    }
  }
  return best;
}

const QUALITY_SUFFIX = /\s*(quality|status)$/i;

export function previewCsv(text: string): Preview {
  // Drop a UTF-8 BOM and a possibly cut-off last line (we only read the first bytes).
  const clean = text.replace(/^﻿/, "");
  const lines = clean.split(/\r?\n/).filter((l) => l.trim() !== "");
  if (clean.length >= PREVIEW_BYTES - 1 && lines.length > 1) lines.pop();
  const warnings: string[] = [];
  if (lines.length === 0) {
    return { kind: "csv", delimiter: ",", format: "wide", header: [], rows: [], tags: [], warnings: ["The file is empty."] };
  }

  const delimiter = detectDelimiter(lines[0]!);
  const header = splitCsvLine(lines[0]!, delimiter);
  const rows = lines.slice(1).map((l) => splitCsvLine(l, delimiter));
  const lower = header.map((h) => h.toLowerCase());
  const format: ExportFormat = header.includes("tag") && header.includes("value") ? "long" : "wide";

  if (!header.includes("timestamp")) {
    const guess = lower.findIndex((h) => /time|date/.test(h));
    warnings.push(
      guess >= 0
        ? `The time column is called "${header[guess]}"; the default layout expects "timestamp". Rename it, or ask us for an export profile.`
        : 'No "timestamp" column found. The default layout expects columns timestamp, tag, value (long) or timestamp plus one column per tag (wide).',
    );
  }
  if (format === "wide" && (lower.includes("tag") || lower.includes("value") || lower.includes("tagname"))) {
    warnings.push('This looks like a long export, but the columns aren\'t named exactly "tag" and "value".');
  }
  if (header.length < 2) warnings.push(`Only one column was found. Is the file separated by "${delimiter}"?`);

  let tags: string[];
  if (format === "long") {
    const ti = header.indexOf("tag");
    tags = [...new Set(rows.map((r) => r[ti] ?? "").filter(Boolean))];
  } else {
    tags = header.filter((h) => h !== "timestamp" && !QUALITY_SUFFIX.test(h));
  }

  return { kind: "csv", delimiter, format, header, rows: rows.slice(0, PREVIEW_ROWS), tags, warnings };
}

export async function previewFile(file: File): Promise<Preview | ParquetPreview> {
  if (isParquet(file.name)) {
    return { kind: "parquet", warnings: [] };
  }
  return previewCsv(await file.slice(0, PREVIEW_BYTES).text());
}

export function delimiterName(d: string): string {
  return { ",": "comma", ";": "semicolon", "\t": "tab", "|": "pipe" }[d] ?? `"${d}"`;
}
