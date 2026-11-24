import { ApiError, type ImportReport } from "@driplytics/contracts";
import {
  Banner,
  Card,
  CardBody,
  CardHeader,
  Chip,
  LedgerBar,
  PageHeader,
  ReadOnlyNote,
  Stat,
  Steps,
  TBody,
  TD,
  TH,
  THead,
  TR,
  Table,
  TableCaption,
  buttonVariants,
  formatBytes,
  formatCount,
  formatDateTime,
} from "@driplytics/ui";
import { Download, Upload } from "lucide-react";
import Link from "next/link";
import { notFound } from "next/navigation";

import { ImportLive, RetryImport } from "@/components/imports/ImportLive";
import { ReasonsTable } from "@/components/imports/ReasonsTable";
import { getAppContext, load } from "@/lib/api/server";
import { importStatus } from "@/lib/imports";

export const metadata = { title: "Import report" };

const STEPS = ["Upload export", "Review import", "Confirm tags", "First findings"];

async function orNotFound<T>(p: Promise<T>): Promise<T> {
  try {
    return await p;
  } catch (e) {
    if (e instanceof ApiError && (e.status === 404 || e.status === 422)) notFound();
    throw e;
  }
}

export default async function ImportReportPage({ params }: { params: Promise<{ importId: string }> }) {
  const { importId } = await params;
  const { tenant, api } = await getAppContext();
  if (!tenant || !api) notFound();

  const path = { params: { path: { import_id: importId } } };
  const imp = await orNotFound(load(api.GET("/api/v1/imports/{import_id}", path)));
  const site = tenant.sites.find((s) => s.id === imp.site_id);
  const tz = site?.timezone ?? "UTC";
  const report = imp.status === "succeeded" ? await orNotFound(load(api.GET("/api/v1/imports/{import_id}/report", path))) : null;
  const status = importStatus(imp);
  const allMapped = report ? report.scoring_allowed : false;

  return (
    <>
      <PageHeader
        title={<span className="font-mono">{imp.original_filename ?? "Import"}</span>}
        description={
          <>
            Uploaded {formatDateTime(imp.created_at, tz)}
            {imp.size_bytes != null ? ` · ${formatBytes(imp.size_bytes)}` : ""} · <Chip tone={status.tone}>{status.label}</Chip>
          </>
        }
        breadcrumbs={[site?.name ?? "Site", "Data", "Imports", "Report"]}
        actions={
          <>
            {report && report.rejected > 0 ? (
              <a
                href={`/api/v1/imports/${imp.id}/rejected-examples.csv`}
                download
                className={buttonVariants({ variant: "secondary", size: "md" })}
              >
                <Download /> Rejected examples (CSV)
              </a>
            ) : null}
            <Link href="/data/imports/new" className={buttonVariants({ variant: report ? "secondary" : "ghost", size: "md" })}>
              <Upload /> Upload another
            </Link>
          </>
        }
      />
      <Steps steps={STEPS} current={report ? (allMapped ? 3 : 2) : 1} className="mb-(--dl-gap)" />

      <div className="flex flex-col gap-(--dl-gap)">
        {imp.status === "queued" || imp.status === "running" ? (
          <Card>
            <CardHeader title="Importing" description="Every value is checked: timestamps, quality, units, daylight saving and duplicates." />
            <CardBody>
              <ImportLive initial={imp} />
            </CardBody>
          </Card>
        ) : null}

        {imp.status === "failed" ? (
          <Banner tone="warning" title="The import failed" action={<RetryImport importId={imp.id} />}>
            {imp.error ?? "No error message was recorded."}
          </Banner>
        ) : null}

        {imp.status === "pending" ? (
          <Banner
            tone="neutral"
            title="The file never finished uploading"
            action={<Link className={buttonVariants({ variant: "primary", size: "sm" })} href="/data/imports/new">Upload again</Link>}
          >
            The upload was interrupted before the import started.
          </Banner>
        ) : null}

        {report ? <ReportBody report={report} timezone={tz} /> : null}
      </div>
      <ReadOnlyNote className="mt-6" />
    </>
  );
}

function ReportBody({ report, timezone }: { report: ImportReport; timezone: string }) {
  const unmapped = Object.entries(report.unmapped_tags).sort((a, b) => b[1] - a[1]);
  return (
    <>
      {report.scoring_allowed ? (
        <Banner tone="success" title="Ready for scoring">
          Every tag in this file is mapped. Leak-by and pump checks run on this data in Phase 1.
        </Banner>
      ) : (
        <Banner
          tone="warning"
          title={
            unmapped.length
              ? `Scoring is blocked: ${unmapped.length} unmapped tag${unmapped.length === 1 ? "" : "s"}`
              : "Scoring is blocked"
          }
          action={
            <Link href="/data/tag-mapping" className={buttonVariants({ variant: "primary", size: "sm" })}>
              Map these tags
            </Link>
          }
        >
          {unmapped.length ? (
            <span>
              {unmapped.map(([tag, n], i) => (
                <span key={tag}>
                  {i ? ", " : ""}
                  <span className="font-mono">{tag}</span> ({formatCount(n)} values)
                </span>
              ))}
              . Map them, then import the file again.
            </span>
          ) : (
            report.scoring_blocked_reasons.join("; ")
          )}
        </Banner>
      )}

      <Card>
        <CardHeader
          title="Every value accounted for"
          description="Each value in the file was accepted, rejected with a reason, or recognized as an exact duplicate."
        />
        <CardBody className="flex flex-col gap-5">
          <LedgerBar
            total={report.total_values}
            segments={[
              { label: "accepted", value: report.accepted, tone: "success" },
              { label: "rejected", value: report.rejected, tone: "warning" },
              { label: "duplicates", value: report.duplicates, tone: "neutral" },
            ]}
          />
          <div className="grid grid-cols-2 gap-4 border-t border-border pt-4 sm:grid-cols-4">
            <Stat label="Format" value={report.format === "long" ? "Long" : "Wide"} hint={report.format === "long" ? "one row per tag and time" : "one column per tag"} />
            <Stat label="Local time zone" value={<span className="text-base">{report.timezone}</span>} />
            <Stat label="Tags" value={formatCount(report.tags.length)} hint={unmapped.length ? `+ ${unmapped.length} unmapped` : "all mapped"} />
            <Stat
              label="Processing time"
              value={`${report.elapsed_s < 1 ? report.elapsed_s.toFixed(2) : report.elapsed_s.toFixed(1)} s`}
              hint={`${formatCount(report.values_per_second)} values/s`}
            />
          </div>
          {report.accepted_uncertain > 0 ? (
            <p className="text-sm text-fg-muted">
              {formatCount(report.accepted_uncertain)} accepted value{report.accepted_uncertain === 1 ? " is" : "s are"} marked
              Uncertain by the historian; kept, and flagged in the checks.
            </p>
          ) : null}
        </CardBody>
      </Card>

      {report.rejected > 0 ? (
        <Card>
          <CardHeader
            title="Why values were rejected"
            description="Sorted by count. Open a reason to see example rows exactly as they appear in the file."
          />
          <CardBody>
            <ReasonsTable byReason={report.rejected_by_reason} examples={report.rejected_examples} rejected={report.rejected} />
          </CardBody>
        </Card>
      ) : null}

      <Card>
        <CardHeader title="Clock changes and meter events" description="Handled automatically; listed so you can check them." />
        <CardBody>
          <EventList report={report} timezone={timezone} />
        </CardBody>
      </Card>

      <Card>
        <CardHeader title="Tags in this file" description={`Times shown in ${timezone}.`} />
        <CardBody>
          <Table>
            <TableCaption>Per-tag summary</TableCaption>
            <THead>
              <TR>
                <TH>Raw tag</TH>
                <TH>Name</TH>
                <TH>Role</TH>
                <TH numeric>Values in</TH>
                <TH numeric>Rows out</TH>
                <TH>Unit</TH>
                <TH>From</TH>
                <TH>To</TH>
              </TR>
            </THead>
            <TBody>
              {report.tags.map((t) => (
                <TR key={t.tag}>
                  <TD mono>{t.raw_tag}</TD>
                  <TD mono>{t.tag}</TD>
                  <TD>
                    <Chip>{t.role.replaceAll("_", " ")}</Chip>
                  </TD>
                  <TD numeric>{formatCount(t.accepted_inputs)}</TD>
                  <TD numeric>{formatCount(t.output_rows)}</TD>
                  <TD>{t.unit || "—"}</TD>
                  <TD>{t.first_utc ? formatDateTime(t.first_utc, timezone) : "—"}</TD>
                  <TD>{t.last_utc ? formatDateTime(t.last_utc, timezone) : "—"}</TD>
                </TR>
              ))}
            </TBody>
          </Table>
        </CardBody>
      </Card>
    </>
  );
}

function EventList({ report, timezone }: { report: ImportReport; timezone: string }) {
  const items: string[] = [];
  const first = report.dst.ambiguous_first_pass ?? 0;
  const second = report.dst.ambiguous_second_pass ?? 0;
  const gap = report.dst.nonexistent_local_time ?? 0;
  if (first + second > 0) {
    items.push(
      `Clocks went back: ${formatCount(first + second)} values fell in the repeated hour. ` +
        `They were placed in time by their order in the file (${formatCount(first)} in the first pass, ${formatCount(second)} in the second).`,
    );
  }
  if (gap > 0) {
    items.push(
      `Clocks sprang forward: ${formatCount(gap)} value${gap === 1 ? " has a local time" : "s have local times"} inside the skipped hour, so they were rejected.`,
    );
  }
  for (const e of report.totalizer_events) {
    items.push(
      `${e.raw_tag} ${e.event === "rollover" ? "rolled over" : "was reset"} at ${formatDateTime(e.timestamp_utc, timezone)} ` +
        `(${formatCount(e.from_value)} → ${formatCount(e.to_value)}); the flow rate was computed across it.`,
    );
  }
  if (report.totalizer_gaps > 0) {
    items.push(
      `${formatCount(report.totalizer_gaps)} totalizer gap${report.totalizer_gaps === 1 ? " was" : "s were"} longer than the allowed gap, so no flow rate was computed across ${report.totalizer_gaps === 1 ? "it" : "them"}.`,
    );
  }
  if (report.blank_cells_ignored > 0) {
    items.push(`${formatCount(report.blank_cells_ignored)} blank cells in the wide export were skipped, as configured.`);
  }
  if (!items.length) return <p className="text-sm text-fg-muted">No clock changes or meter rollovers in this file.</p>;
  return (
    <ul className="flex list-disc flex-col gap-2 pl-5 text-sm">
      {items.map((t) => (
        <li key={t}>{t}</li>
      ))}
    </ul>
  );
}
