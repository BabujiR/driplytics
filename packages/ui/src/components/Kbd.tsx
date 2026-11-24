import type { ComponentProps } from "react";

import { cn } from "../lib/cn";

/** A keyboard key: <Kbd>Ctrl</Kbd> <Kbd>K</Kbd> */
export function Kbd({ className, ...props }: ComponentProps<"kbd">) {
  return (
    <kbd
      className={cn(
        "inline-flex h-5 min-w-5 items-center justify-center rounded-sm border border-border-strong border-b-2",
        "bg-surface px-1 font-mono text-[0.6875rem] font-medium text-fg-muted",
        className,
      )}
      {...props}
    />
  );
}
