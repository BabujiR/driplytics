"use client";

import { Dialog, Input, Kbd } from "@driplytics/ui";
import { Search } from "lucide-react";
import { useEffect, useState } from "react";

/** Ctrl/Cmd+K search: a placeholder until search over tags, assets and findings arrives (Phase 1). */
export function CommandMenu() {
  const [open, setOpen] = useState(false);
  const [mac, setMac] = useState(false);

  useEffect(() => {
    setMac(/Mac|iPhone|iPad/.test(navigator.platform));
    const onKey = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setOpen((o) => !o);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  return (
    <>
      <button
        type="button"
        onClick={() => setOpen(true)}
        className="flex h-(--dl-control-h) w-full max-w-sm items-center gap-2 rounded-md border border-border bg-surface px-3 text-sm text-fg-subtle shadow-sm hover:border-border-strong"
      >
        <Search aria-hidden className="size-4" />
        <span className="flex-1 truncate text-left">Search tags, assets, findings…</span>
        <span className="hidden items-center gap-0.5 sm:flex">
          <Kbd>{mac ? "⌘" : "Ctrl"}</Kbd>
          <Kbd>K</Kbd>
        </span>
      </button>
      <Dialog
        open={open}
        onOpenChange={setOpen}
        title="Search"
        description="Search across tags, assets, findings and settings arrives in Phase 1."
      >
        <Input autoFocus placeholder="e.g. FV-101, filter gallery, leak-by" aria-label="Search" disabled />
        <p className="mt-3 text-xs text-fg-muted">
          Tip: press <Kbd>{mac ? "⌘" : "Ctrl"}</Kbd> <Kbd>K</Kbd> anywhere to open search, <Kbd>Esc</Kbd> to close.
        </p>
      </Dialog>
    </>
  );
}
