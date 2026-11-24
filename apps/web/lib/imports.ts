import type { Import, ImportStatus } from "@driplytics/contracts";
import type { Tone } from "@driplytics/ui";

/** Plain-words label and tone for an import status (red stays reserved for top-$ losses). */
export function importStatus(imp: Pick<Import, "status" | "progress">): { label: string; tone: Tone } {
  const map: Record<ImportStatus, { label: string; tone: Tone }> = {
    pending: { label: "Waiting for upload", tone: "neutral" },
    uploaded: { label: "Uploaded", tone: "info" },
    queued: { label: "Queued", tone: "info" },
    running: { label: `Importing ${Math.round(imp.progress * 100)} %`, tone: "info" },
    succeeded: { label: "Imported", tone: "success" },
    failed: { label: "Failed", tone: "warning" },
    cancelled: { label: "Cancelled", tone: "neutral" },
  };
  return map[imp.status];
}
