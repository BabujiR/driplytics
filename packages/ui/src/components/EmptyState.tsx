import type { LucideIcon } from "lucide-react";
import type { ReactNode } from "react";

import { cn } from "../lib/cn";

interface EmptyStateProps {
  icon?: LucideIcon;
  title: ReactNode;
  description?: ReactNode;
  /** The one thing to do next, e.g. an "Upload an export" button. */
  action?: ReactNode;
  className?: string;
}

/** Nothing here yet: say why and what to do next. */
export function EmptyState({ icon: Icon, title, description, action, className }: EmptyStateProps) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center gap-3 rounded-lg border border-dashed border-border-strong",
        "bg-surface px-6 py-12 text-center",
        className,
      )}
    >
      {Icon ? (
        <span className="flex size-11 items-center justify-center rounded-full bg-primary-soft text-primary-soft-fg">
          <Icon aria-hidden className="size-5" />
        </span>
      ) : null}
      <div className="max-w-md">
        <h3 className="text-base font-semibold text-fg">{title}</h3>
        {description ? <p className="mt-1 text-sm text-fg-muted">{description}</p> : null}
      </div>
      {action ? <div className="mt-1">{action}</div> : null}
    </div>
  );
}
