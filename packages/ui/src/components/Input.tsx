import { type ComponentProps, type ReactElement, cloneElement, isValidElement, useId } from "react";

import { cn } from "../lib/cn";

const control =
  "w-full rounded-md border border-border-strong bg-surface px-3 text-sm text-fg shadow-sm " +
  "placeholder:text-fg-subtle disabled:cursor-not-allowed disabled:opacity-50 " +
  "aria-invalid:border-critical aria-invalid:outline-critical";

export function Input({ className, ...props }: ComponentProps<"input">) {
  return <input className={cn(control, "h-(--dl-control-h)", className)} {...props} />;
}

export function Select({ className, children, ...props }: ComponentProps<"select">) {
  return (
    <select className={cn(control, "h-(--dl-control-h) pr-8", className)} {...props}>
      {children}
    </select>
  );
}

export function Textarea({ className, ...props }: ComponentProps<"textarea">) {
  return <textarea className={cn(control, "min-h-20 py-2", className)} {...props} />;
}

export function Label({ className, ...props }: ComponentProps<"label">) {
  return <label className={cn("text-sm font-medium text-fg", className)} {...props} />;
}

interface ControlProps {
  id?: string;
  "aria-invalid"?: boolean;
  "aria-describedby"?: string;
}

interface FieldProps {
  label: string;
  /** Help text under the control. */
  hint?: string;
  /** Error message; marks the control invalid and is read by screen readers. */
  error?: string;
  className?: string;
  /** One control (Input, Select, Textarea); its id and aria attributes are filled in. */
  children: ReactElement<ControlProps>;
}

/** Label + control + hint/error, wired for screen readers. */
export function Field({ label, hint, error, className, children }: FieldProps) {
  const id = useId();
  const hintId = hint ? `${id}-hint` : undefined;
  const errorId = error ? `${id}-error` : undefined;
  const control = isValidElement(children)
    ? cloneElement(children, {
        id: children.props.id ?? id,
        "aria-invalid": error ? true : undefined,
        "aria-describedby": [errorId, hintId].filter(Boolean).join(" ") || undefined,
      })
    : children;
  return (
    <div className={cn("flex flex-col gap-1.5", className)}>
      <Label htmlFor={children.props.id ?? id}>{label}</Label>
      {control}
      {error ? (
        <p id={errorId} className="text-xs text-critical-fg">
          {error}
        </p>
      ) : null}
      {hint ? (
        <p id={hintId} className="text-xs text-fg-muted">
          {hint}
        </p>
      ) : null}
    </div>
  );
}
