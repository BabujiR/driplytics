import type { ReactNode } from "react";

import { cn } from "../lib/cn";
import type { Tone } from "./tone";

interface StatProps {
  label: ReactNode;
  value: ReactNode;
  /** Unit after the value: "/ year", "gpm". */
  unit?: ReactNode;
  /** One line of context under the value. */
  hint?: ReactNode;
  /** Colors the value; use sparingly (critical only for top-$ losses). */
  tone?: Tone;
  className?: string;
}

const valueTone: Record<Tone, string> = {
  neutral: "text-fg",
  info: "text-info-fg",
  success: "text-success-fg",
  warning: "text-warning-fg",
  critical: "text-critical-fg",
};

/** A headline number: "Estimated loss $84.2k / year". */
export function Stat({ label, value, unit, hint, tone = "neutral", className }: StatProps) {
  return (
    <div className={cn("flex min-w-0 flex-col gap-0.5", className)}>
      <span className="text-xs font-medium text-fg-muted">{label}</span>
      <span className={cn("text-2xl font-semibold tabular-nums tracking-tight", valueTone[tone])}>
        {value}
        {unit ? <span className="ml-1 text-sm font-normal text-fg-muted">{unit}</span> : null}
      </span>
      {hint ? <span className="text-xs text-fg-muted">{hint}</span> : null}
    </div>
  );
}
