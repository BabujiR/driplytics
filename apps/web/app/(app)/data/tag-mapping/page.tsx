import {
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
} from "@driplytics/ui";
import { Tags } from "lucide-react";

import { getAppContext, load } from "@/lib/api/server";

export const metadata = { title: "Tag mapping" };

export default async function TagMappingPage() {
  const { site, api } = await getAppContext();
  if (!site || !api) return <PageHeader title="Tag mapping" description="Add a site first." />;

  const tags = await load(api.GET("/api/v1/sites/{site_id}/tag-mappings", { params: { path: { site_id: site.id } } }));
  const unmapped = tags.filter((t) => t.role === null).length;

  return (
    <>
      <PageHeader
        title="Tag mapping"
        description="What each historian tag means: its role, canonical name and units. Scoring needs every required tag mapped."
        breadcrumbs={[site.name, "Data", "Tag mapping"]}
        actions={
          tags.length ? (
            <Chip tone={unmapped ? "warning" : "success"}>
              {unmapped ? `${unmapped} unmapped` : "All tags mapped"}
            </Chip>
          ) : null
        }
      />
      {tags.length === 0 ? (
        <EmptyState
          icon={Tags}
          title="No tags yet"
          description="Tags appear after the first import or a tag_mapping.csv upload. The mapping assistant arrives in Phase 1."
        />
      ) : (
        <Table>
          <TableCaption>Tags of {site.name}</TableCaption>
          <THead>
            <TR>
              <TH>Raw tag</TH>
              <TH>Role</TH>
              <TH>Canonical name</TH>
              <TH>Units</TH>
              <TH>States (true / false)</TH>
              <TH>Source</TH>
            </TR>
          </THead>
          <TBody>
            {tags.map((t) => (
              <TR key={t.tag_id}>
                <TD mono>{t.raw_tag}</TD>
                <TD>{t.role ? <Chip>{t.role.replaceAll("_", " ")}</Chip> : <Chip tone="warning">Unmapped</Chip>}</TD>
                <TD mono>{t.canonical_tag ?? "—"}</TD>
                <TD>{t.source_unit ? `${t.source_unit}${t.target_unit && t.target_unit !== t.source_unit ? ` → ${t.target_unit}` : ""}` : "—"}</TD>
                <TD mono>{t.state_true ? `${t.state_true} / ${t.state_false ?? "—"}` : "—"}</TD>
                <TD className="text-fg-muted">{t.source ?? "—"}</TD>
              </TR>
            ))}
          </TBody>
        </Table>
      )}
      <ReadOnlyNote className="mt-4" />
    </>
  );
}
