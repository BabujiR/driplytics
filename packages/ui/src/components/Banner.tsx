import type { LucideIcon } from "lucide-react";
import type { ComponentProps, ReactNode } from "react";

import { cn } from "../lib/cn";
import { type Tone, toneClasses, toneIcons } from "./tone";

interface BannerProps extends Omit<ComponentProps<"div">, "title"> {
  tone?: Tone;
  title: ReactNode;
  icon?: LucideIcon;
  /** A button that fixes the problem, e.g. "Map these tags". */
  action?: ReactNode;
}

/**
 * A message across the content: "Scoring is blocked: 1 unmapped tag". Critical banners are announced
 * immediately (role="alert"); the rest politely (role="status").
 */
export function Banner({ tone = "info", title, icon, action, className, children, ...props }: BannerProps) {
  const Icon = icon ?? toneIcons[tone];
  return (
    <div
      role={tone === "critical" ? "alert" : "status"}
      className={cn("flex items-start gap-3 rounded-lg border px-4 py-3", toneClasses[tone].soft, className)}
      {...props}
    >
      <Icon aria-hidden className="mt-0.5 size-5 shrink-0" />
      <div className="min-w-0 flex-1">
        <p className="font-semibold">{title}</p>
        {children ? <div className="mt-0.5 text-sm opacity-90">{children}</div> : null}
      </div>
      {action ? <div className="shrink-0 self-center">{action}</div> : null}
    </div>
  );
}
