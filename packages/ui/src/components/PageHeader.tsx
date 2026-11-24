import { ChevronRight } from "lucide-react";
import type { ReactNode } from "react";

import { cn } from "../lib/cn";

interface PageHeaderProps {
  title: ReactNode;
  description?: ReactNode;
  /** Site › Area › Asset trail; the last item is the current page. */
  breadcrumbs?: ReactNode[];
  actions?: ReactNode;
  className?: string;
}

/** Top of every page: answer first (the title says what this page tells you), actions on the right. */
export function PageHeader({ title, description, breadcrumbs, actions, className }: PageHeaderProps) {
  return (
    <header className={cn("mb-(--dl-gap) flex flex-wrap items-end gap-4", className)}>
      <div className="min-w-0 flex-1">
        {breadcrumbs?.length ? (
          <nav aria-label="Breadcrumb" className="mb-1">
            <ol className="flex flex-wrap items-center gap-1 text-xs text-fg-muted">
              {breadcrumbs.map((b, i) => (
                <li key={i} className="flex items-center gap-1">
                  {i > 0 ? <ChevronRight aria-hidden className="size-3 text-fg-subtle" /> : null}
                  <span aria-current={i === breadcrumbs.length - 1 ? "page" : undefined}>{b}</span>
                </li>
              ))}
            </ol>
          </nav>
        ) : null}
        <h1 className="text-xl font-semibold tracking-tight text-fg">{title}</h1>
        {description ? <p className="mt-1 max-w-3xl text-sm text-fg-muted">{description}</p> : null}
      </div>
      {actions ? <div className="flex shrink-0 flex-wrap items-center gap-2">{actions}</div> : null}
    </header>
  );
}

/** CLAUDE.md §12.1 (5): shown on data and connector screens for plant IT and operators. */
export function ReadOnlyNote({ className }: { className?: string }) {
  return (
    <p className={cn("flex items-center gap-1.5 text-xs text-fg-muted", className)}>
      <span aria-hidden>🔒</span>
      Read-only: Driplytics never writes to your control system.
    </p>
  );
}
