"use client";

import { Upload } from "lucide-react";
import { type DragEvent, type ReactNode, useId, useState } from "react";

import { cn } from "../lib/cn";

interface FileDropProps {
  title: ReactNode;
  hint?: ReactNode;
  /** e.g. ".csv,.txt,.parquet" */
  accept?: string;
  disabled?: boolean;
  onFile: (file: File) => void;
  /** Smaller variant for secondary files (e.g. a tag mapping). */
  compact?: boolean;
  className?: string;
}

/** Drag and drop a file, or click (or press Enter/Space) to browse. */
export function FileDrop({ title, hint, accept, disabled, onFile, compact, className }: FileDropProps) {
  const id = useId();
  const [over, setOver] = useState(false);

  const onDrop = (e: DragEvent) => {
    e.preventDefault();
    setOver(false);
    const file = e.dataTransfer.files[0];
    if (file && !disabled) onFile(file);
  };

  return (
    <label
      htmlFor={id}
      onDragOver={(e) => {
        e.preventDefault();
        if (!disabled) setOver(true);
      }}
      onDragLeave={() => setOver(false)}
      onDrop={onDrop}
      className={cn(
        "flex cursor-pointer flex-col items-center justify-center gap-2 rounded-lg border-2 border-dashed text-center transition-colors",
        "border-border-strong bg-surface hover:border-primary hover:bg-primary-soft/40",
        "has-[input:focus-visible]:outline-2 has-[input:focus-visible]:outline-offset-2 has-[input:focus-visible]:outline-focus",
        compact ? "px-4 py-4" : "px-6 py-10",
        over && "border-primary bg-primary-soft",
        disabled && "pointer-events-none opacity-50",
        className,
      )}
    >
      <input
        id={id}
        type="file"
        accept={accept}
        disabled={disabled}
        className="sr-only"
        onChange={(e) => {
          const file = e.target.files?.[0];
          if (file) onFile(file);
          e.target.value = ""; // allow choosing the same file again
        }}
      />
      {!compact ? (
        <span className="flex size-11 items-center justify-center rounded-full bg-primary-soft text-primary-soft-fg">
          <Upload aria-hidden className="size-5" />
        </span>
      ) : null}
      <span className={cn("font-semibold text-fg", compact ? "text-sm" : "text-base")}>{title}</span>
      {hint ? <span className="text-sm text-fg-muted">{hint}</span> : null}
    </label>
  );
}
