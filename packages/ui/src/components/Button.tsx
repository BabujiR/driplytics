import { cva, type VariantProps } from "class-variance-authority";
import type { ComponentProps } from "react";

import { cn } from "../lib/cn";
import { Spinner } from "./Spinner";

export const buttonVariants = cva(
  "inline-flex shrink-0 select-none items-center justify-center gap-2 whitespace-nowrap rounded-md border font-medium " +
    "transition-colors disabled:pointer-events-none disabled:opacity-50 [&_svg]:size-4 [&_svg]:shrink-0",
  {
    variants: {
      variant: {
        primary: "border-transparent bg-primary text-primary-fg shadow-sm hover:bg-primary-hover",
        secondary: "border-border-strong bg-surface text-fg shadow-sm hover:bg-surface-2",
        ghost: "border-transparent bg-transparent text-fg-muted hover:bg-surface-2 hover:text-fg",
        danger: "border-transparent bg-critical text-white shadow-sm hover:opacity-90",
      },
      size: {
        sm: "h-(--dl-control-h-sm) px-2.5 text-xs",
        md: "h-(--dl-control-h) px-3.5 text-sm",
        lg: "h-(--dl-control-h-lg) px-5 text-base",
        icon: "size-(--dl-control-h) p-0",
      },
    },
    defaultVariants: { variant: "secondary", size: "md" },
  },
);

export interface ButtonProps extends ComponentProps<"button">, VariantProps<typeof buttonVariants> {
  /** Shows a spinner, disables the button and sets aria-busy. */
  loading?: boolean;
}

/** Buttons: one primary action per view; secondary for the rest; ghost for toolbars; danger to delete. */
export function Button({ className, variant, size, loading = false, disabled, children, type, ...props }: ButtonProps) {
  return (
    <button
      type={type ?? "button"}
      className={cn(buttonVariants({ variant, size }), className)}
      disabled={disabled || loading}
      aria-busy={loading || undefined}
      {...props}
    >
      {loading ? <Spinner /> : null}
      {children}
    </button>
  );
}
