import { cn } from "../lib/cn";
import { type Tone, toneClasses } from "./tone";

interface ProgressBarProps {
  /** 0..1; leave undefined for "working, no estimate" (animated). */
  value?: number;
  /** Accessible name, e.g. "Uploading historian_long.csv". */
  label: string;
  tone?: Tone;
  className?: string;
}

export function ProgressBar({ value, label, tone = "info", className }: ProgressBarProps) {
  const pct = value === undefined ? undefined : Math.round(Math.min(1, Math.max(0, value)) * 100);
  return (
    <div
      role="progressbar"
      aria-label={label}
      aria-valuemin={0}
      aria-valuemax={100}
      aria-valuenow={pct}
      className={cn("h-2 w-full overflow-hidden rounded-full bg-surface-3", className)}
    >
      <div
        className={cn(
          "h-full rounded-full transition-[width] duration-300",
          toneClasses[tone].solid,
          pct === undefined && "w-1/3 animate-pulse",
        )}
        style={pct === undefined ? undefined : { width: `${pct}%` }}
      />
    </div>
  );
}
