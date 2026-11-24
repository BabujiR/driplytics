import type { ComponentProps } from "react";

import { cn } from "../lib/cn";

/** Data table. Row height and padding follow the density mode; numbers use tabular figures. */
export function Table({ className, ...props }: ComponentProps<"table">) {
  return (
    <div className="w-full overflow-x-auto rounded-lg border border-border bg-surface">
      <table className={cn("w-full border-collapse text-sm", className)} {...props} />
    </div>
  );
}

export function TableCaption({ className, ...props }: ComponentProps<"caption">) {
  return <caption className={cn("sr-only", className)} {...props} />;
}

export function THead({ className, ...props }: ComponentProps<"thead">) {
  return <thead className={cn("bg-surface-2", className)} {...props} />;
}

export function TBody({ className, ...props }: ComponentProps<"tbody">) {
  return <tbody className={cn("[&>tr:last-child]:border-b-0", className)} {...props} />;
}

export function TR({ className, ...props }: ComponentProps<"tr">) {
  return <tr className={cn("h-(--dl-row-h) border-b border-border hover:bg-surface-2/60", className)} {...props} />;
}

interface CellProps {
  /** Right-aligned, tabular figures: use for every number column. */
  numeric?: boolean;
  /** Monospace: tag names and raw values. */
  mono?: boolean;
}

export function TH({ className, numeric, mono, ...props }: ComponentProps<"th"> & CellProps) {
  return (
    <th
      scope="col"
      className={cn(
        "px-(--dl-cell-px) py-(--dl-cell-py) text-left text-xs font-semibold tracking-wide text-fg-muted",
        numeric && "text-right",
        mono && "font-mono",
        className,
      )}
      {...props}
    />
  );
}

export function TD({ className, numeric, mono, ...props }: ComponentProps<"td"> & CellProps) {
  return (
    <td
      className={cn(
        "px-(--dl-cell-px) py-(--dl-cell-py) align-middle text-fg",
        numeric && "text-right tabular-nums",
        mono && "font-mono text-[0.8125rem]",
        className,
      )}
      {...props}
    />
  );
}
