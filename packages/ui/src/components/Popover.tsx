"use client";

import type { ComponentProps, ReactNode } from "react";

import { cn } from "../lib/cn";

interface PopoverProps extends Omit<ComponentProps<"div">, "popover"> {
  /** Must match the trigger's `popoverTarget`. */
  id: string;
  children: ReactNode;
}

/**
 * A menu or panel on the browser's Popover API: the trigger is any button with
 * `popoverTarget={id}`; Esc and clicking outside close it. Positioned by the caller
 * (e.g. `className="top-14 right-4"`).
 */
export function Popover({ id, className, children, ...props }: PopoverProps) {
  return (
    <div
      id={id}
      popover="auto"
      className={cn(
        "fixed m-0 min-w-56 rounded-lg border border-border bg-surface p-1 text-fg shadow-lg inset-auto",
        className,
      )}
      {...props}
    >
      {children}
    </div>
  );
}

export function MenuItem({ className, ...props }: ComponentProps<"button">) {
  return (
    <button
      type="button"
      className={cn(
        "flex w-full items-center gap-2 rounded-md px-2.5 py-2 text-left text-sm text-fg hover:bg-surface-2",
        "disabled:opacity-50 [&_svg]:size-4 [&_svg]:text-fg-muted",
        className,
      )}
      {...props}
    />
  );
}

export function MenuLabel({ className, ...props }: ComponentProps<"div">) {
  return <div className={cn("px-2.5 pt-2 pb-1 text-xs font-medium text-fg-subtle", className)} {...props} />;
}

export function MenuSeparator() {
  return <div role="separator" className="my-1 h-px bg-border" />;
}
