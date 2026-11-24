"use client";

import { errorMessage } from "@driplytics/contracts";
import { Banner, FileDrop, useToast } from "@driplytics/ui";
import { useRouter } from "next/navigation";
import { useState } from "react";

/** PUT /sites/{id}/tag-mappings/csv: until the mapping assistant arrives (Phase 1). */
export async function uploadMapping(siteId: string, file: File): Promise<number> {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`/api/v1/sites/${siteId}/tag-mappings/csv`, { method: "PUT", body: form });
  const body: unknown = await res.json().catch(() => null);
  if (!res.ok) throw new Error(errorMessage(res.status, body));
  return (body as { mapped_tags: number }).mapped_tags;
}

/** Standalone mapping upload (Tag mapping page). */
export function MappingUpload({ siteId }: { siteId: string }) {
  const router = useRouter();
  const { toast } = useToast();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  return (
    <div className="flex flex-col gap-2">
      <FileDrop
        compact
        accept=".csv"
        disabled={busy}
        title={busy ? "Saving the mapping…" : "Upload a tag_mapping.csv"}
        hint="raw_tag, canonical_tag, role, units, states. Every line is checked first; any problem rejects the whole file."
        onFile={async (file) => {
          setBusy(true);
          setError(null);
          try {
            const n = await uploadMapping(siteId, file);
            toast({ title: "Tag mapping saved", description: `${n} tags mapped`, tone: "success" });
            router.refresh();
          } catch (e) {
            setError(e instanceof Error ? e.message : String(e));
          } finally {
            setBusy(false);
          }
        }}
      />
      {error ? (
        <Banner tone="warning" title="The mapping was not saved">
          <span className="whitespace-pre-line">{error}</span>
        </Banner>
      ) : null}
    </div>
  );
}
