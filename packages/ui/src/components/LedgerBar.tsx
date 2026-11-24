import { formatCount } from "../lib/format";
import { cn } from "../lib/cn";
import { type Tone, toneClasses } from "./tone";

export interface LedgerSegment {
  label: string;
  value: number;
  tone: Tone;
}

interface LedgerBarProps {
  total: number;
  segments: LedgerSegment[];
  className?: string;
}

/**
 * The accounting invariant made visible (CLAUDE.md §12.4): one stacked bar, a legend with numbers,
 * and the equation written out, e.g. "5,179 = 5,157 accepted + 19 rejected + 3 duplicates".
 * Tiny segments keep a sliver so they stay visible; the legend carries the exact numbers.
 */
export function LedgerBar({ total, segments, className }: LedgerBarProps) {
  const equation = `${formatCount(total)} = ${segments.map((s) => `${formatCount(s.value)} ${s.label}`).join(" + ")}`;
  return (
    <figure className={cn("flex flex-col gap-3", className)}>
      <div role="img" aria-label={equation} className="flex h-7 w-full gap-0.5 overflow-hidden rounded-md">
        {segments
          .filter((s) => s.value > 0)
          .map((s) => (
            <div
              key={s.label}
              className={cn("h-full", toneClasses[s.tone].solid)}
              style={{ flexGrow: s.value, flexBasis: 0, minWidth: "0.375rem" }}
              title={`${formatCount(s.value)} ${s.label}`}
            />
          ))}
      </div>
      <ul className="flex flex-wrap gap-x-6 gap-y-1 text-sm">
        {segments.map((s) => (
          <li key={s.label} className="flex items-center gap-2">
            <span aria-hidden className={cn("size-3 rounded-sm", toneClasses[s.tone].solid)} />
            <span className="font-semibold tabular-nums">{formatCount(s.value)}</span>
            <span className="text-fg-muted">
              {s.label} ({total ? ((s.value / total) * 100).toFixed(s.value / total < 0.01 && s.value ? 2 : 1) : "0"} %)
            </span>
          </li>
        ))}
      </ul>
      <figcaption className="font-mono text-sm text-fg">{equation}</figcaption>
    </figure>
  );
}
