"use client";

import { errorMessage, unwrap } from "@driplytics/contracts";
import {
  Banner,
  Button,
  Card,
  CardBody,
  CardHeader,
  Chip,
  FileDrop,
  ProgressBar,
  ReadOnlyNote,
  Steps,
  TBody,
  TD,
  TH,
  THead,
  TR,
  Table,
  formatBytes,
  formatCount,
} from "@driplytics/ui";
import { FileSpreadsheet, Tags, X } from "lucide-react";
import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";

import { browserApi } from "@/lib/api/browser";
import { type ParquetPreview, type Preview, delimiterName, previewFile } from "@/lib/upload/detect";
import { putWithProgress } from "@/lib/upload/put";

import { uploadMapping } from "./MappingUpload";

const ACCEPT = ".csv,.txt,.parquet,.pq";
const STEPS = ["Upload export", "Review import", "Confirm tags", "First findings"];

type Phase =
  | { name: "choose" }
  | { name: "ready" }
  | { name: "uploading"; fraction: number }
  | { name: "starting" }
  | { name: "error"; message: string };

interface Props {
  siteId: string;
  siteName: string;
  timezone: string;
}

export function UploadWizard({ siteId, siteName, timezone }: Props) {
  const router = useRouter();
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<Preview | ParquetPreview | null>(null);
  const [mapping, setMapping] = useState<File | null>(null);
  const [phase, setPhase] = useState<Phase>({ name: "choose" });
  const abort = useRef<AbortController | null>(null);
  const busy = phase.name === "uploading" || phase.name === "starting";

  // Warn before leaving the page mid-upload.
  useEffect(() => {
    if (!busy) return;
    const warn = (e: BeforeUnloadEvent) => e.preventDefault();
    window.addEventListener("beforeunload", warn);
    return () => window.removeEventListener("beforeunload", warn);
  }, [busy]);

  const choose = async (f: File) => {
    setFile(f);
    setPreview(null);
    setPhase({ name: "ready" });
    try {
      setPreview(await previewFile(f));
    } catch {
      setPreview({ kind: "parquet", warnings: ["The file could not be read in the browser."] });
    }
  };

  const reset = () => {
    abort.current?.abort();
    setFile(null);
    setPreview(null);
    setPhase({ name: "choose" });
  };

  const start = async () => {
    if (!file) return;
    const api = browserApi();
    abort.current = new AbortController();
    try {
      if (mapping) {
        setPhase({ name: "uploading", fraction: 0 });
        await uploadMapping(siteId, mapping);
      }
      // 1. Create the import and get a one-time upload link.
      const created = await unwrap(
        api.POST("/api/v1/sites/{site_id}/imports", {
          params: { path: { site_id: siteId } },
          body: { filename: file.name, size_bytes: file.size },
        }),
      );
      // 2. Upload straight to object storage.
      setPhase({ name: "uploading", fraction: 0 });
      await putWithProgress(
        created.upload,
        file,
        (fraction) => setPhase({ name: "uploading", fraction }),
        abort.current.signal,
      );
      // 3. Queue the import; the report page follows its progress.
      setPhase({ name: "starting" });
      await unwrap(
        api.POST("/api/v1/imports/{import_id}/start", { params: { path: { import_id: created.import.id } } }),
      );
      router.push(`/data/imports/${created.import.id}`);
    } catch (e) {
      if (abort.current?.signal.aborted) return; // cancelled by the user: reset() already cleared the form
      setPhase({ name: "error", message: e instanceof Error ? e.message : errorMessage(0, e) });
    }
  };

  return (
    <div className="flex flex-col gap-(--dl-gap)">
      <Steps steps={STEPS} current={0} />

      {!file ? (
        <FileDrop
          accept={ACCEPT}
          onFile={choose}
          title="Drag and drop a CSV or Parquet export here"
          hint="PI or IP.21 exports, long or wide format, up to 5 GB per file, or click to browse"
        />
      ) : (
        <Card>
          <CardHeader
            title={
              <span className="flex items-center gap-2">
                <FileSpreadsheet aria-hidden className="size-5 text-fg-muted" />
                <span className="font-mono">{file.name}</span>
              </span>
            }
            description={`${formatBytes(file.size)} · for ${siteName}`}
            actions={
              <Button variant="ghost" size="sm" onClick={reset} disabled={phase.name === "starting"}>
                <X /> {busy ? "Cancel" : "Choose another file"}
              </Button>
            }
          />
          <CardBody className="flex flex-col gap-4">
            <PreviewPanel preview={preview} timezone={timezone} />
          </CardBody>
        </Card>
      )}

      {file ? (
        <Card>
          <CardHeader
            title={
              <span className="flex items-center gap-2">
                <Tags aria-hidden className="size-5 text-fg-muted" />
                Tag mapping (optional)
              </span>
            }
            description="Already mapped this site's tags? Skip this. Otherwise add a tag_mapping.csv so values can be checked and scored. Unmapped tags are listed in the import report."
          />
          <CardBody>
            {mapping ? (
              <div className="flex items-center gap-3 text-sm">
                <Chip tone="info">{mapping.name}</Chip>
                <span className="text-fg-muted">saved before the import starts</span>
                <Button variant="ghost" size="sm" onClick={() => setMapping(null)} disabled={busy}>
                  Remove
                </Button>
              </div>
            ) : (
              <FileDrop compact accept=".csv" onFile={setMapping} disabled={busy} title="Add tag_mapping.csv" />
            )}
          </CardBody>
        </Card>
      ) : null}

      {phase.name === "error" ? (
        <Banner tone="warning" title="The import did not start">
          {phase.message}
        </Banner>
      ) : null}

      {phase.name === "uploading" || phase.name === "starting" ? (
        <div className="flex flex-col gap-2" aria-live="polite">
          <p className="text-sm text-fg-muted">
            {phase.name === "uploading"
              ? `Uploading straight to storage… ${Math.round(phase.fraction * 100)} %`
              : "Upload complete. Queueing the import…"}
          </p>
          <ProgressBar
            label="Upload progress"
            value={phase.name === "uploading" ? phase.fraction : undefined}
            tone={phase.name === "starting" ? "success" : "info"}
          />
        </div>
      ) : null}

      <div className="flex flex-wrap items-center gap-3">
        <ReadOnlyNote className="flex-1" />
        <Button variant="primary" size="lg" disabled={!file || busy} loading={busy} onClick={start}>
          {phase.name === "error" ? "Try again" : "Start import"}
        </Button>
      </div>
    </div>
  );
}

function PreviewPanel({ preview, timezone }: { preview: Preview | ParquetPreview | null; timezone: string }) {
  if (!preview) return <ProgressBar label="Reading the first rows" />;
  if (preview.kind === "parquet") {
    return (
      <p className="text-sm text-fg-muted">
        Parquet file: columns and rows are read on the server. Timestamps without a zone are read as{" "}
        <strong className="text-fg">{timezone}</strong>.
      </p>
    );
  }
  return (
    <>
      <div className="flex flex-wrap items-center gap-2 text-sm">
        <span className="text-fg-muted">We detected:</span>
        <Chip tone="info">{preview.format === "long" ? "Long format (one row per tag and time)" : "Wide format (one column per tag)"}</Chip>
        <Chip>{delimiterName(preview.delimiter)}-separated</Chip>
        <Chip>
          {formatCount(preview.tags.length)} {preview.tags.length === 1 ? "tag" : "tags"}
          {preview.format === "long" ? " in the first rows" : ""}
        </Chip>
        <span className="text-fg-muted">
          · timestamps read as <strong className="text-fg">{timezone}</strong> (the site&apos;s zone)
        </span>
      </div>
      {preview.warnings.map((w) => (
        <Banner key={w} tone="warning" title="Check this before importing">
          {w}
        </Banner>
      ))}
      {preview.header.length ? (
        <Table>
          <THead>
            <TR>
              {preview.header.map((h, i) => (
                <TH key={i} mono>
                  {h}
                </TH>
              ))}
            </TR>
          </THead>
          <TBody>
            {preview.rows.map((r, i) => (
              <TR key={i}>
                {preview.header.map((_, j) => (
                  <TD key={j} mono>
                    {r[j] ?? ""}
                  </TD>
                ))}
              </TR>
            ))}
          </TBody>
        </Table>
      ) : null}
    </>
  );
}
