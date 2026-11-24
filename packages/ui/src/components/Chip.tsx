import type { LucideIcon } from "lucide-react";
import type { ComponentProps } from "react";

import { cn } from "../lib/cn";
import { type Tone, toneClasses } from "./tone";

interface ChipProps extends ComponentProps<"span"> {
  tone?: Tone;
  /** Optional icon before the label. The label is always text: color is never the only signal. */
  icon?: LucideIcon;
}

/** Status and category labels: "New", "Verifying", "High confidence", "Unmapped". */
export function Chip({ tone = "neutral", icon: Icon, className, children, ...props }: ChipProps) {
  return (
    <span
      className={cn(
        "inline-flex h-6 items-center gap-1 whitespace-nowrap rounded-full border px-2 text-xs font-medium",
        toneClasses[tone].soft,
        className,
      )}
      {...props}
    >
      {Icon ? <Icon aria-hidden className="size-3.5" /> : null}
      {children}
    </span>
  );
}
