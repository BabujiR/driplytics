/**
 * Number, money and time formatting (CLAUDE.md §12.5): always units, sensible rounding,
 * times in the site's zone with the zone shown. Pure functions, no React.
 */

const LOCALE = "en-US";

/** 5179 → "5,179" */
export function formatCount(n: number): string {
  return new Intl.NumberFormat(LOCALE, { maximumFractionDigits: 0 }).format(n);
}

/** 84200 → "$84.2k", 1250000 → "$1.25M", 950 → "$950". Add a unit suffix such as "/yr" with `per`. */
export function formatDollars(n: number, per?: string): string {
  const abs = Math.abs(n);
  let text: string;
  if (abs >= 999_500) text = `$${trim(n / 1_000_000, abs >= 10_000_000 ? 1 : 2)}M`;
  else if (abs >= 999.5) text = `$${trim(n / 1_000, abs >= 100_000 ? 0 : 1)}k`;
  else text = `$${Math.round(n)}`;
  if (n < 0) text = `-${text.replace("-", "")}`;
  return per ? `${text}/${per}` : text;
}

/** A range when uncertainty is real: (6000, 9000, "yr") → "$6k–$9k/yr" */
export function formatDollarRange(low: number, high: number, per?: string): string {
  const r = `${formatDollars(low)}–${formatDollars(high)}`;
  return per ? `${r}/${per}` : r;
}

function trim(x: number, digits: number): string {
  return x.toFixed(digits).replace(/\.0+$|(\.\d*?)0+$/, "$1");
}

/** 0.4567 → "45.7 %" */
export function formatPercent(fraction: number, digits = 1): string {
  return `${trim(fraction * 100, digits)} %`;
}

/** 222428 → "217 KB" (1024-based, like file managers) */
export function formatBytes(n: number): string {
  const units = ["bytes", "KB", "MB", "GB", "TB"];
  let v = n;
  let i = 0;
  while (v >= 1024 && i < units.length - 1) {
    v /= 1024;
    i += 1;
  }
  return i === 0 ? `${formatCount(v)} bytes` : `${trim(v, v >= 100 ? 0 : 1)} ${units[i]}`;
}

/** A value with its unit: (3.96, "gpm") → "3.96 gpm" (up to `digits` decimals) */
export function formatQuantity(value: number, unit: string, digits = 2): string {
  const v = new Intl.NumberFormat(LOCALE, { maximumFractionDigits: digits }).format(value);
  return unit ? `${v} ${unit}` : v;
}

/**
 * A timestamp in the site's time zone, with the zone shown:
 * ("2026-11-01T05:30:00Z", "America/New_York") → "Nov 1, 2026, 1:30 AM EDT"
 */
export function formatDateTime(iso: string | Date, timeZone: string): string {
  const d = typeof iso === "string" ? new Date(iso) : iso;
  return new Intl.DateTimeFormat(LOCALE, {
    timeZone,
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
    timeZoneName: "short",
  })
    .format(d)
    .replace(/[\u202f\u00a0]/g, " "); // ICU versions differ; keep server and browser output identical
}

/** "3 min ago", "2 h ago", "5 d ago" (for data freshness) */
export function formatRelative(iso: string | Date, now: Date = new Date()): string {
  const d = typeof iso === "string" ? new Date(iso) : iso;
  const s = Math.round((now.getTime() - d.getTime()) / 1000);
  if (s < 45) return "just now";
  if (s < 3600) return `${Math.round(s / 60)} min ago`;
  if (s < 86400) return `${Math.round(s / 3600)} h ago`;
  return `${Math.round(s / 86400)} d ago`;
}

/** "Alice Riverbend" → "AR", "bob@lakeside.test" → "BO" */
export function initials(nameOrEmail: string): string {
  const base = nameOrEmail.includes("@") ? (nameOrEmail.split("@")[0] ?? "") : nameOrEmail;
  const parts = base.split(/[\s._-]+/).filter(Boolean);
  const letters = parts.length >= 2 ? (parts[0]?.[0] ?? "") + (parts[1]?.[0] ?? "") : base.slice(0, 2);
  return letters.toUpperCase() || "?";
}
