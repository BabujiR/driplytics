import { Check } from "lucide-react";

import { cn } from "../lib/cn";

interface StepsProps {
  steps: string[];
  /** 0-based index of the current step; earlier steps show as done. */
  current: number;
  className?: string;
}

/** Progress through a flow, e.g. Upload export → Review import → Confirm tags → First findings. */
export function Steps({ steps, current, className }: StepsProps) {
  return (
    <ol className={cn("flex flex-wrap gap-2", className)}>
      {steps.map((label, i) => {
        const state = i < current ? "done" : i === current ? "current" : "todo";
        return (
          <li
            key={label}
            aria-current={state === "current" ? "step" : undefined}
            className={cn(
              "flex min-w-40 flex-1 items-center gap-2 rounded-md border px-3 py-2 text-sm",
              state === "current" && "border-primary bg-primary-soft font-medium text-primary-soft-fg",
              state === "done" && "border-border bg-surface-2 text-fg-muted",
              state === "todo" && "border-border bg-surface text-fg-muted",
            )}
          >
            <span
              className={cn(
                "flex size-5 shrink-0 items-center justify-center rounded-full text-[0.6875rem] font-semibold",
                state === "current" ? "bg-primary text-primary-fg" : "bg-surface-3 text-fg-muted",
                state === "done" && "bg-success text-white",
              )}
            >
              {state === "done" ? <Check aria-hidden className="size-3" /> : i + 1}
            </span>
            {label}
            {state === "done" ? <span className="sr-only">(done)</span> : null}
          </li>
        );
      })}
    </ol>
  );
}
