"use client";

import type { ImportDetail } from "@driplytics/contracts";
import { unwrap } from "@driplytics/contracts";
import { Banner, Button, ProgressBar } from "@driplytics/ui";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { browserApi } from "@/lib/api/browser";
import { importStatus } from "@/lib/imports";

const FINISHED = new Set(["succeeded", "failed", "cancelled"]);

/** Follows a queued or running import, then reloads the page to show the report. */
export function ImportLive({ initial }: { initial: Pick<ImportDetail, "id" | "status" | "progress"> }) {
  const router = useRouter();
  const [imp, setImp] = useState(initial);
  const [slow, setSlow] = useState(false);

  useEffect(() => {
    let stop = false;
    let status = initial.status;
    const started = Date.now();
    const tick = async () => {
      try {
        const next = await unwrap(
          browserApi().GET("/api/v1/imports/{import_id}", { params: { path: { import_id: initial.id } } }),
        );
        if (stop) return;
        setImp(next);
        status = next.status;
        if (FINISHED.has(next.status)) {
          router.refresh();
          return;
        }
      } catch {
        // keep polling: a restart of the API shouldn't break the page
      }
      if (!stop) {
        setSlow(Date.now() - started > 60_000 && status === "queued");
        setTimeout(tick, 1500);
      }
    };
    const t = setTimeout(tick, 1000);
    return () => {
      stop = true;
      clearTimeout(t);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps -- start once per import
  }, [initial.id]);

  const s = importStatus(imp);
  return (
    <div className="flex flex-col gap-3" aria-live="polite">
      <p className="text-sm text-fg-muted">
        {imp.status === "queued" ? "Waiting for a worker to pick up the import…" : `${s.label}: checking every value…`}
      </p>
      <ProgressBar label="Import progress" value={imp.status === "running" ? imp.progress : undefined} />
      {slow ? (
        <Banner tone="warning" title="Still waiting for a worker">
          Is the worker running? Check with <code className="font-mono">docker compose ps worker</code>.
        </Banner>
      ) : null}
    </div>
  );
}

/** Restart a failed import (or one whose queue message was lost). */
export function RetryImport({ importId, label = "Try again" }: { importId: string; label?: string }) {
  const router = useRouter();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  return (
    <div className="flex flex-col items-start gap-2">
      <Button
        variant="primary"
        size="sm"
        loading={busy}
        onClick={async () => {
          setBusy(true);
          setError(null);
          try {
            await unwrap(browserApi().POST("/api/v1/imports/{import_id}/start", { params: { path: { import_id: importId } } }));
            router.refresh();
          } catch (e) {
            setError(e instanceof Error ? e.message : String(e));
          } finally {
            setBusy(false);
          }
        }}
      >
        {label}
      </Button>
      {error ? <p className="text-sm text-warning-fg">{error}</p> : null}
    </div>
  );
}
