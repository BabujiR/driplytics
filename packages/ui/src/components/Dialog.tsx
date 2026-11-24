"use client";

import { X } from "lucide-react";
import { type ReactNode, useEffect, useId, useRef } from "react";

import { cn } from "../lib/cn";
import { Button } from "./Button";

interface DialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title: ReactNode;
  description?: ReactNode;
  children?: ReactNode;
  /** Buttons, right-aligned. Put the main action last. */
  footer?: ReactNode;
  className?: string;
}

/**
 * Modal dialog on the native <dialog> element: the browser traps focus, closes on Esc and restores
 * focus to the trigger. Clicking the backdrop also closes it.
 */
export function Dialog({ open, onOpenChange, title, description, children, footer, className }: DialogProps) {
  const ref = useRef<HTMLDialogElement>(null);
  const titleId = useId();
  const descId = useId();

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    if (open && !el.open) el.showModal();
    if (!open && el.open) el.close();
  }, [open]);

  return (
    <dialog
      ref={ref}
      aria-labelledby={titleId}
      aria-describedby={description ? descId : undefined}
      onClose={() => onOpenChange(false)}
      onClick={(e) => {
        if (e.target === e.currentTarget) onOpenChange(false); // backdrop
      }}
      className={cn(
        "m-auto w-[min(32rem,calc(100vw-2rem))] rounded-lg border border-border bg-surface p-0 text-fg shadow-lg",
        className,
      )}
    >
      <div className="flex items-start gap-3 px-5 pt-5">
        <div className="min-w-0 flex-1">
          <h2 id={titleId} className="text-lg font-semibold">
            {title}
          </h2>
          {description ? (
            <p id={descId} className="mt-1 text-sm text-fg-muted">
              {description}
            </p>
          ) : null}
        </div>
        <Button variant="ghost" size="icon" aria-label="Close" onClick={() => onOpenChange(false)}>
          <X />
        </Button>
      </div>
      {children ? <div className="px-5 py-4">{children}</div> : <div className="h-4" />}
      {footer ? (
        <div className="flex justify-end gap-2 border-t border-border bg-surface-2 px-5 py-3">{footer}</div>
      ) : null}
    </dialog>
  );
}
