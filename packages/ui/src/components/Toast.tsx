"use client";

import { X } from "lucide-react";
import { type ReactNode, createContext, useCallback, useContext, useMemo, useState } from "react";

import { cn } from "../lib/cn";
import { type Tone, toneClasses, toneIcons } from "./tone";

export interface ToastOptions {
  title: string;
  description?: string;
  tone?: Tone;
  /** Milliseconds before it hides; 0 keeps it until closed. Default 5000 (critical: 0). */
  duration?: number;
}

interface ToastItem extends Required<Omit<ToastOptions, "description">> {
  id: number;
  description?: string;
}

interface ToastApi {
  toast: (options: ToastOptions) => void;
  dismiss: (id: number) => void;
}

const ToastContext = createContext<ToastApi | null>(null);

let nextId = 1;

/** Wrap the app once. Toasts are announced by screen readers (polite; critical ones assertive). */
export function ToastProvider({ children }: { children: ReactNode }) {
  const [items, setItems] = useState<ToastItem[]>([]);

  const dismiss = useCallback((id: number) => setItems((all) => all.filter((t) => t.id !== id)), []);

  const toast = useCallback(
    ({ title, description, tone = "info", duration }: ToastOptions) => {
      const id = nextId++;
      const ms = duration ?? (tone === "critical" ? 0 : 5000);
      setItems((all) => [...all.slice(-4), { id, title, description, tone, duration: ms }]);
      if (ms > 0) setTimeout(() => dismiss(id), ms);
    },
    [dismiss],
  );

  const api = useMemo(() => ({ toast, dismiss }), [toast, dismiss]);

  return (
    <ToastContext.Provider value={api}>
      {children}
      <ToastViewport items={items} onDismiss={dismiss} />
    </ToastContext.Provider>
  );
}

export function useToast(): ToastApi {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error("useToast must be used inside <ToastProvider>");
  return ctx;
}

export function ToastViewport({ items, onDismiss }: { items: ToastItem[]; onDismiss: (id: number) => void }) {
  const polite = items.filter((t) => t.tone !== "critical");
  const urgent = items.filter((t) => t.tone === "critical");
  return (
    <div className="pointer-events-none fixed right-4 bottom-4 z-50 flex w-[min(24rem,calc(100vw-2rem))] flex-col gap-2">
      <div role="status" aria-live="polite" className="flex flex-col gap-2">
        {polite.map((t) => (
          <ToastCard key={t.id} item={t} onDismiss={onDismiss} />
        ))}
      </div>
      <div role="alert" aria-live="assertive" className="flex flex-col gap-2">
        {urgent.map((t) => (
          <ToastCard key={t.id} item={t} onDismiss={onDismiss} />
        ))}
      </div>
    </div>
  );
}

export function ToastCard({ item, onDismiss }: { item: ToastItem; onDismiss?: (id: number) => void }) {
  const Icon = toneIcons[item.tone];
  return (
    <div
      className={cn(
        "pointer-events-auto flex animate-toast-in items-start gap-3 rounded-lg border bg-surface p-3 shadow-md",
        "border-border",
      )}
    >
      <Icon aria-hidden className={cn("mt-0.5 size-5 shrink-0", toneClasses[item.tone].icon)} />
      <div className="min-w-0 flex-1">
        <p className="text-sm font-semibold text-fg">{item.title}</p>
        {item.description ? <p className="mt-0.5 text-sm text-fg-muted">{item.description}</p> : null}
      </div>
      {onDismiss ? (
        <button
          type="button"
          aria-label="Dismiss"
          onClick={() => onDismiss(item.id)}
          className="rounded-sm p-0.5 text-fg-subtle hover:bg-surface-2 hover:text-fg"
        >
          <X aria-hidden className="size-4" />
        </button>
      ) : null}
    </div>
  );
}
