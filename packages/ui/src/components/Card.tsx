import type { ComponentProps, ReactNode } from "react";

import { cn } from "../lib/cn";

export function Card({ className, ...props }: ComponentProps<"section">) {
  return <section className={cn("rounded-lg border border-border bg-surface shadow-sm", className)} {...props} />;
}

interface CardHeaderProps extends Omit<ComponentProps<"header">, "title"> {
  title: ReactNode;
  description?: ReactNode;
  /** Buttons on the right. */
  actions?: ReactNode;
}

export function CardHeader({ title, description, actions, className, ...props }: CardHeaderProps) {
  return (
    <header className={cn("flex items-start gap-4 px-(--dl-card-p) pt-(--dl-card-p)", className)} {...props}>
      <div className="min-w-0 flex-1">
        <h2 className="text-base font-semibold text-fg">{title}</h2>
        {description ? <p className="mt-0.5 text-sm text-fg-muted">{description}</p> : null}
      </div>
      {actions ? <div className="flex shrink-0 items-center gap-2">{actions}</div> : null}
    </header>
  );
}

export function CardBody({ className, ...props }: ComponentProps<"div">) {
  return <div className={cn("p-(--dl-card-p)", className)} {...props} />;
}

export function CardFooter({ className, ...props }: ComponentProps<"footer">) {
  return (
    <footer
      className={cn("flex items-center gap-2 border-t border-border px-(--dl-card-p) py-3", className)}
      {...props}
    />
  );
}
