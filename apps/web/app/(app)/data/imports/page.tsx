import {
  Banner,
  Chip,
  EmptyState,
  PageHeader,
  ReadOnlyNote,
  TBody,
  TD,
  TH,
  THead,
  TR,
  Table,
  TableCaption,
  formatBytes,
  formatDateTime,
} from "@driplytics/ui";
import { Upload } from "lucide-react";

import { getAppContext, load } from "@/lib/api/server";
import { importStatus } from "@/lib/imports";

export const metadata = { title: "Imports" };

export default async function ImportsPage() {
  const { site, api } = await getAppContext();
  if (!site || !api) return <PageHeader title="Imports" description="Add a site first." />;

  const imports = await load(api.GET("/api/v1/sites/{site_id}/imports", { params: { path: { site_id: site.id } } }));

  return (
    <>
      <PageHeader
        title="Imports"
        description="Historian exports uploaded for this site. Every value is accounted for: accepted, rejected with a reason, or a duplicate."
        breadcrumbs={[site.name, "Data", "Imports"]}
      />
      <Banner tone="info" title="Uploading from the browser comes next (P0-17)" className="mb-(--dl-gap)">
        Until then, run <code className="font-mono">.\tasks.ps1 demo</code> to import the sample export for this site.
      </Banner>

      {imports.length === 0 ? (
        <EmptyState
          icon={Upload}
          title="No imports yet"
          description="Upload a PI or IP.21 export (CSV or Parquet, long or wide format) to see its import report."
        />
      ) : (
        <Table>
          <TableCaption>Imports for {site.name}, newest first</TableCaption>
          <THead>
            <TR>
              <TH>File</TH>
              <TH>Status</TH>
              <TH numeric>Size</TH>
              <TH>Uploaded</TH>
              <TH>Finished</TH>
            </TR>
          </THead>
          <TBody>
            {imports.map((imp) => {
              const s = importStatus(imp);
              return (
                <TR key={imp.id}>
                  <TD mono>{imp.original_filename ?? "—"}</TD>
                  <TD>
                    <Chip tone={s.tone}>{s.label}</Chip>
                    {imp.error ? <p className="mt-1 max-w-md text-xs text-fg-muted">{imp.error}</p> : null}
                  </TD>
                  <TD numeric>{imp.size_bytes != null ? formatBytes(imp.size_bytes) : "—"}</TD>
                  <TD>{formatDateTime(imp.created_at, site.timezone)}</TD>
                  <TD>{imp.finished_at ? formatDateTime(imp.finished_at, site.timezone) : "—"}</TD>
                </TR>
              );
            })}
          </TBody>
        </Table>
      )}
      <ReadOnlyNote className="mt-4" />
    </>
  );
}
